from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint, Enum, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
import enum
from app.config.database import Base


class BorrowStatus(str, enum.Enum):
    """Borrow record status enumeration"""
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"


class Borrow(Base):
    """Borrow records model for tracking book loans"""
    __tablename__ = "borrow_records"
    
    borrow_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey('books.book_id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Date fields
    borrowed_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    due_date = Column(DateTime, nullable=False, index=True)  # Calculated as borrowed_date + 14 days
    return_date = Column(DateTime, nullable=True)  # Null until book is returned
    
    # Fine calculation
    fine_amount = Column(Float, default=0.0, nullable=False)  # Rs 5 per day after due date
    
    # Status
    status = Column(Enum(BorrowStatus), default=BorrowStatus.ACTIVE, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="borrow_records")
    book = relationship("Books", back_populates="borrow_records")
    
    def calculate_fine(self) -> float:
        """Calculate fine if book is returned late (Rs 5 per day)"""
        if not self.return_date or not self.due_date:
            return 0.0
        
        # Ensure both datetimes are timezone-aware for comparison
        return_date = self.return_date if self.return_date.tzinfo else self.return_date.replace(tzinfo=timezone.utc)
        due_date = self.due_date if self.due_date.tzinfo else self.due_date.replace(tzinfo=timezone.utc)
        
        if return_date > due_date:
            days_late = (return_date - due_date).days
            return max(0, days_late * 5.0)  # Rs 5 per day
        return 0.0
    
    def mark_returned(self):
        """Mark book as returned and calculate fine"""
        self.return_date = datetime.now(timezone.utc)
        self.fine_amount = self.calculate_fine()
        self.status = BorrowStatus.RETURNED
    
    def is_overdue(self) -> bool:
        """Check if book is overdue"""
        if self.return_date:  # Already returned
            return False
        return datetime.now(timezone.utc) > self.due_date