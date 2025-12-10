from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import LONGTEXT
from datetime import datetime, timezone
from app.config.database import Base


class StaticContent(Base):
    __tablename__ = "book_static_content"
    
    content_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey('books.book_id', ondelete='CASCADE'), unique=True, nullable=False, index=True)
    summary_text = Column(LONGTEXT)  # Changed to LONGTEXT for large content
    qa_json = Column(LONGTEXT)  # Changed to LONGTEXT for large Q&A
    podcast_script = Column(LONGTEXT)  # Changed to LONGTEXT for large scripts
    audio_url = Column(String(500), unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationship to access book details
    book = relationship("Books", back_populates="static_content")
