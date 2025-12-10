from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class BorrowCreateSchema(BaseModel):
    """Schema for creating a borrow record"""
    book_title: str
    user_email: EmailStr


class StudentReturnSchema(BaseModel):
    """Schema for student return request"""
    book_title: str
    user_email: EmailStr


class BorrowSchema(BaseModel):
    """Schema for borrow record response"""
    borrow_id: int
    book_id: int
    user_id: int
    borrowed_date: datetime
    due_date: datetime
    return_date: Optional[datetime] = None
    fine_amount: float = 0.0
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  