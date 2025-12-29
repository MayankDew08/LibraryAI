from pydantic import BaseModel, field_validator
from typing import Optional, List
from fastapi import UploadFile


class BookCreateSchema(BaseModel):
    """Schema for creating a book - files will be uploaded separately"""
    title: str
    author: str
    total_copies: int
    categories: List[str]  # List of category names
    
    @field_validator('categories')
    @classmethod
    def validate_categories(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one category is required')
        # Remove duplicates and strip whitespace
        return list(set([cat.strip() for cat in v if cat.strip()]))
    
class BookUpdateSchema(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    total_copies: Optional[int] = None
    available_copies: Optional[int] = None
    categories: Optional[List[str]] = None

class BookResponseSchema(BaseModel):
    book_id: int
    title: str
    author: str
    cover_image: Optional[str] = None
    pdf_url: Optional[str] = None
    total_copies: int
    available_copies: int
    categories: List[str] = []  # List of category names
    
    class Config:
        from_attributes = True