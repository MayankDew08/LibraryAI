from pydantic import BaseModel
from typing import Optional
from fastapi import UploadFile


class BookCreateSchema(BaseModel):
    """Schema for creating a book - files will be uploaded separately"""
    title: str
    author: str
    total_copies: int
    
class BookUpdateSchema(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    total_copies: Optional[int] = None
    available_copies: Optional[int] = None

class BookResponseSchema(BaseModel):
    book_id: int
    title: str
    author: str
    cover_image: Optional[str] = None
    pdf_url: Optional[str] = None
    total_copies: int
    available_copies: int
    
    class Config:
        from_attributes = True