from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StaticContentCreateSchema(BaseModel):
    """Schema for creating static content"""
    book_id: int
    summary_text: Optional[str] = None
    qa_json: Optional[str] = None  # JSON string
    podcast_script: Optional[str] = None
    audio_url: Optional[str] = None


class StaticContentUpdateSchema(BaseModel):
    """Schema for updating static content"""
    summary_text: Optional[str] = None
    qa_json: Optional[str] = None
    podcast_script: Optional[str] = None
    audio_url: Optional[str] = None


class StaticContentSchema(BaseModel):
    """Schema for static content response"""
    content_id: int
    book_id: int
    pdf_url: str 
    summary_text: Optional[str] = None
    qa_json: Optional[str] = None
    podcast_script: Optional[str] = None
    audio_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True