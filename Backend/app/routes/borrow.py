from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.borrow import borrow_book, student_return_book, admin_verify_return
from app.schemas.borrow_schemas import BorrowCreateSchema, BorrowSchema, StudentReturnSchema
from app.models.borrow import Borrow
from app.models.books import Books
from app.models.users import User
from app.models.admin import Admin
from app.services.auth import get_current_admin
from pydantic import BaseModel
from datetime import timezone

router = APIRouter(prefix="/borrow", tags=["borrow"])


class AdminVerifySchema(BaseModel):
    """Schema for admin fine verification"""
    fine_paid: bool


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_borrow(
    borrow_data: BorrowCreateSchema,
    db: Session = Depends(get_db)
):
    """Borrow a book using book title and user email (max 5 books per user)"""
    try:
        result = borrow_book(db, borrow_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/student/return")
def student_return(
    return_data: StudentReturnSchema,
    db: Session = Depends(get_db)
):
    """Student returns a book using book title and email. Auto-deleted if no fine, otherwise awaits admin verification."""
    try:
        result = student_return_book(db, return_data)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{borrow_id}", response_model=BorrowSchema)
def get_borrow(
    borrow_id: int,
    db: Session = Depends(get_db)
):
    """Get borrow record by ID"""
    borrow = db.query(Borrow).filter(Borrow.borrow_id == borrow_id).first()
    if not borrow:
        raise HTTPException(status_code=404, detail="Borrow record not found")
    return borrow


@router.get("/user/email/{user_email}")
def get_user_borrows(
    user_email: str,
    db: Session = Depends(get_db)
):
    """Get all borrow records for a user by email"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User with email '{user_email}' not found")
    
    borrows = db.query(Borrow).filter(Borrow.user_id == user.id).all()
    
    # Enrich with book and user details
    result = []
    for borrow in borrows:
        book = db.query(Books).filter(Books.book_id == borrow.book_id).first()
        result.append({
            "borrow_id": borrow.borrow_id,
            "user_name": user.name,
            "user_email": user.email,
            "book_title": book.title if book else "Unknown",
            "author": book.author if book else "Unknown",
            "borrowed_date": borrow.borrowed_date,
            "due_date": borrow.due_date,
            "return_date": borrow.return_date,
            "fine_amount": borrow.fine_amount,
            "status": borrow.status.value if hasattr(borrow.status, 'value') else str(borrow.status),
            "created_at": borrow.created_at,
            "updated_at": borrow.updated_at
        })
    
    return result


@router.get("/admin/all-borrows")
def get_all_user_borrows(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get all borrow records with user names, emails, book titles, dates, and fines"""
    # Get all borrow records
    borrows = db.query(Borrow).all()
    
    result = []
    for borrow in borrows:
        user = db.query(User).filter(User.id == borrow.user_id).first()
        book = db.query(Books).filter(Books.book_id == borrow.book_id).first()
        
        result.append({
            "borrow_id": borrow.borrow_id,
            "user_name": user.name if user else "Unknown",
            "user_email": user.email if user else "Unknown",
            "book_title": book.title if book else "Unknown",
            "author": book.author if book else "Unknown",
            "borrowed_date": borrow.borrowed_date,
            "due_date": borrow.due_date,
            "return_date": borrow.return_date,
            "fine_amount": borrow.fine_amount,
            "status": borrow.status.value if hasattr(borrow.status, 'value') else str(borrow.status),
            "created_at": borrow.created_at,
            "updated_at": borrow.updated_at
        })
    
    return {
        "total_records": len(result),
        "borrow_records": result
    }


@router.get("/admin/pending-verifications")
def get_pending_verifications(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Admin views all borrow records awaiting fine verification"""
    # Get all returned books with outstanding fines
    pending = db.query(Borrow).filter(
        Borrow.return_date != None,
        Borrow.fine_amount > 0.0
    ).all()
    
    result = []
    for borrow in pending:
        user = db.query(User).filter(User.id == borrow.user_id).first()
        book = db.query(Books).filter(Books.book_id == borrow.book_id).first()
        
        # Calculate days late
        days_late = 0
        if borrow.return_date and borrow.due_date:
            return_date = borrow.return_date if borrow.return_date.tzinfo else borrow.return_date.replace(tzinfo=timezone.utc)
            due_date = borrow.due_date if borrow.due_date.tzinfo else borrow.due_date.replace(tzinfo=timezone.utc)
            if return_date > due_date:
                days_late = (return_date - due_date).days
        
        result.append({
            "borrow_id": borrow.borrow_id,
            "student_name": user.name if user else "Unknown",
            "student_email": user.email if user else "Unknown",
            "book_title": book.title if book else "Unknown",
            "author": book.author if book else "Unknown",
            "borrowed_date": borrow.borrowed_date,
            "due_date": borrow.due_date,
            "return_date": borrow.return_date,
            "fine_amount": borrow.fine_amount,
            "days_late": days_late,
            "status": "awaiting_verification"
        })
    
    return {
        "total_pending": len(result),
        "pending_verifications": result
    }


@router.post("/admin/verify/{borrow_id}")
def admin_verify_fine_payment(
    borrow_id: int,
    verify_data: AdminVerifySchema,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Admin verifies fine payment and completes return (deletes record)"""
    try:
        result = admin_verify_return(db, borrow_id, verify_data.fine_paid)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{borrow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_borrow(
    borrow_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Delete a borrow record (admin only)"""
    borrow = db.query(Borrow).filter(Borrow.borrow_id == borrow_id).first()
    if not borrow:
        raise HTTPException(status_code=404, detail="Borrow record not found")
    
    db.delete(borrow)
    db.commit()
    return

