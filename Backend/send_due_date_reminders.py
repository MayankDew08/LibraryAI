"""
Send due date reminder emails to students whose books are due tomorrow
Run this script daily (can be set up as a cron job or scheduled task)
"""

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import os

from app.models.borrow import Borrow
from app.models.books import Books
from app.models.users import User
from app.services.email_service import email_service

load_dotenv()

DATABASE_URL = os.getenv(
    "SQLALCHEMY_DATABASE_URL",
    "mysql+mysqldb://root:password@localhost:3306/library_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def send_due_date_reminders():
    """Send email reminders for books due tomorrow"""
    db = SessionLocal()
    
    try:
        # Calculate tomorrow's date (start and end of day)
        tomorrow = datetime.now(timezone.utc).date() + timedelta(days=1)
        tomorrow_start = datetime.combine(tomorrow, datetime.min.time()).replace(tzinfo=timezone.utc)
        tomorrow_end = datetime.combine(tomorrow, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        print(f"\n📧 Sending due date reminders for books due on {tomorrow}")
        print("=" * 60)
        
        # Find all borrows with due date tomorrow and not yet returned
        borrows = db.query(Borrow).filter(
            and_(
                Borrow.due_date >= tomorrow_start,
                Borrow.due_date <= tomorrow_end,
                Borrow.return_date == None
            )
        ).all()
        
        if not borrows:
            print("ℹ️  No books due tomorrow. No reminders to send.")
            return
        
        print(f"📚 Found {len(borrows)} book(s) due tomorrow")
        print()
        
        sent_count = 0
        failed_count = 0
        
        for borrow in borrows:
            # Get user and book details
            user = db.query(User).filter(User.id == borrow.user_id).first()
            book = db.query(Books).filter(Books.book_id == borrow.book_id).first()
            
            if not user or not book:
                print(f"⚠️  Skipping borrow ID {borrow.borrow_id} - user or book not found")
                failed_count += 1
                continue
            
            # Send reminder email
            success = email_service.send_due_date_reminder(
                to_email=user.email,
                user_name=user.name,
                book_title=book.title,
                due_date=borrow.due_date.strftime('%Y-%m-%d')
            )
            
            if success:
                print(f"✅ Sent reminder to {user.name} ({user.email}) for '{book.title}'")
                sent_count += 1
            else:
                print(f"❌ Failed to send reminder to {user.name} ({user.email})")
                failed_count += 1
        
        print()
        print("=" * 60)
        print(f"📊 Summary:")
        print(f"   Total books due tomorrow: {len(borrows)}")
        print(f"   ✅ Reminders sent: {sent_count}")
        print(f"   ❌ Failed: {failed_count}")
        print()
        
    except Exception as e:
        print(f"❌ Error sending reminders: {str(e)}")
    
    finally:
        db.close()


if __name__ == "__main__":
    print("\n🔔 Due Date Reminder Service")
    print("=" * 60)
    send_due_date_reminders()
    print("✅ Done!")
