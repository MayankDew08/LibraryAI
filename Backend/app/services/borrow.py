from sqlalchemy.orm import Session
from app.models.borrow import Borrow
from app.models.books import Books
from app.models.users import User
import app.schemas.borrow_schemas as borrow_schemas
from datetime import datetime, timedelta, timezone
from app.services.email_service import email_service


def borrow_book(db: Session, borrow_data: borrow_schemas.BorrowCreateSchema):
    """Create a new borrow record when a user borrows a book"""
    
    # Find user by email
    user = db.query(User).filter(User.email == borrow_data.user_email).first()
    if not user:
        raise ValueError(f"User with email '{borrow_data.user_email}' not found.")
    
    # Find book by title
    book = db.query(Books).filter(Books.title == borrow_data.book_title).first()
    if not book:
        raise ValueError(f"Book with title '{borrow_data.book_title}' not found.")
    
    # Check active borrows limit (max 5 books)
    active_borrows = db.query(Borrow).filter(
        Borrow.user_id == user.id,
        Borrow.return_date == None
    ).count()
    
    if active_borrows >= 5:
        raise ValueError(f"User '{user.name}' has reached maximum borrow limit of 5 books.")
    
    # Check if user already has this book borrowed
    existing_borrow = db.query(Borrow).filter(
        Borrow.book_id == book.book_id,
        Borrow.user_id == user.id,
        Borrow.return_date == None
    ).first()
    
    if existing_borrow:
        raise ValueError(f"User '{user.name}' has already borrowed '{book.title}' and not returned it yet.")
    
    # Check if book is available
    if book.available_copies <= 0:
        raise ValueError(f"No available copies for '{book.title}'.")
    
    # Create new borrow record with explicit dates
    borrowed_date = datetime.now(timezone.utc)
    due_date = borrowed_date + timedelta(days=14)
    
    new_borrow = Borrow(
        user_id=user.id,
        book_id=book.book_id,
        borrowed_date=borrowed_date,
        due_date=due_date
    )
    
    # Decrease available copies
    book.available_copies -= 1
    
    db.add(new_borrow)
    db.commit()
    db.refresh(new_borrow)
    
    # Send borrow confirmation email
    try:
        email_service.send_borrow_confirmation(
            to_email=str(user.email),
            user_name=str(user.name),
            book_title=str(book.title),
            borrow_date=new_borrow.borrowed_date.strftime('%Y-%m-%d'),
            due_date=new_borrow.due_date.strftime('%Y-%m-%d')
        )
    except Exception as e:
        print(f"⚠️  Failed to send borrow confirmation email: {str(e)}")
    
    return {
        "borrow_id": new_borrow.borrow_id,
        "user_name": user.name,
        "user_email": user.email,
        "book_title": book.title,
        "author": book.author,
        "borrowed_date": new_borrow.borrowed_date,
        "due_date": new_borrow.due_date,
        "return_date": new_borrow.return_date,
        "fine_amount": new_borrow.fine_amount,
        "status": new_borrow.status.value if hasattr(new_borrow.status, 'value') else str(new_borrow.status),
        "message": "Book borrowed successfully",
        "reminder": f"Please return '{book.title}' by {new_borrow.due_date.strftime('%Y-%m-%d')} to avoid fine of Rs 5/day"
    }


def student_return_book(db: Session, return_data: borrow_schemas.StudentReturnSchema):
    """Student requests to return a book - will be marked for admin verification if fine exists"""
    
    # Find user by email
    user = db.query(User).filter(User.email == return_data.user_email).first()
    if not user:
        raise ValueError(f"User with email '{return_data.user_email}' not found.")
    
    # Find book by title
    book = db.query(Books).filter(Books.title == return_data.book_title).first()
    if not book:
        raise ValueError(f"Book with title '{return_data.book_title}' not found.")
    
    # Find active borrow record
    borrow = db.query(Borrow).filter(
        Borrow.user_id == user.id,
        Borrow.book_id == book.book_id,
        Borrow.return_date == None
    ).first()
    
    if not borrow:
        raise ValueError(f"No active borrow record found for '{book.title}' by '{user.name}'.")
    
    # Mark as returned and calculate fine
    borrow.mark_returned()
    
    # If no fine, complete the return and delete the record
    if borrow.fine_amount == 0:
        # Increase available copies
        book.available_copies += 1
        
        # Delete the borrow record
        db.delete(borrow)
        db.commit()
        
        return {
            "message": "Book returned successfully",
            "user_name": user.name,
            "book_title": book.title,
            "borrowed_date": borrow.borrowed_date,
            "return_date": borrow.return_date,
            "fine_amount": 0.0,
            "status": "returned_and_cleared"
        }
    else:
        # Fine exists - save the record for admin verification
        db.commit()
        db.refresh(borrow)
        
        return {
            "message": "Book return recorded. Please pay the fine to complete the return.",
            "user_name": user.name,
            "book_title": book.title,
            "borrowed_date": borrow.borrowed_date,
            "due_date": borrow.due_date,
            "return_date": borrow.return_date,
            "fine_amount": borrow.fine_amount,
            "days_late": (borrow.return_date - borrow.due_date).days,
            "status": "awaiting_fine_payment",
            "note": f"Please pay Rs {borrow.fine_amount:.2f} to admin and provide borrow_id: {borrow.borrow_id} for verification"
        }


def admin_verify_return(db: Session, borrow_id: int, fine_paid: bool):
    """Admin verifies fine payment and completes return"""
    
    borrow = db.query(Borrow).filter(Borrow.borrow_id == borrow_id).first()
    if not borrow:
        raise ValueError(f"Borrow record with ID {borrow_id} not found.")
    
    if borrow.return_date is None:
        raise ValueError("Book has not been returned yet.")
    
    if borrow.fine_amount == 0:
        raise ValueError("No fine exists for this borrow record.")
    
    if not fine_paid:
        raise ValueError("Fine must be paid before completing the return.")
    
    # Get book to update available copies
    book = db.query(Books).filter(Books.book_id == borrow.book_id).first()
    user = db.query(User).filter(User.id == borrow.user_id).first()
    
    if book:
        book.available_copies += 1
    
    # Store details before deletion
    result = {
        "message": "Return verified and completed successfully",
        "borrow_id": borrow.borrow_id,
        "user_name": user.name if user else "Unknown",
        "book_title": book.title if book else "Unknown",
        "fine_paid": borrow.fine_amount,
        "status": "completed"
    }
    
    # Delete the borrow record
    db.delete(borrow)
    db.commit()
    
    return result