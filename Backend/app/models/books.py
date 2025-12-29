from sqlalchemy import Column, Integer, String, Text, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.config.database import Base
from app.models.category import book_categories


class Books(Base):
    """Books model for library inventory"""
    __tablename__ = "books"

    book_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    author = Column(String(255), nullable=False, index=True)
    pdf_url = Column(String(500), unique=True)
    cover_image = Column(String(500))
    total_copies = Column(Integer, nullable=False, default=1)
    available_copies = Column(Integer, nullable=False, default=1)
    is_public = Column(Integer, nullable=False, default=1)  # 1 = public (allow AI), 0 = confidential
    rag_indexed = Column(Integer, nullable=False, default=0)  # 1 = RAG indexed, 0 = not indexed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    borrow_records = relationship("Borrow", back_populates="book", cascade="all, delete-orphan")
    static_content = relationship("StaticContent", back_populates="book", cascade="all, delete-orphan", uselist=False)
    categories = relationship("Category", secondary=book_categories, back_populates="books")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('total_copies >= 0', name='check_total_copies_positive'),
        CheckConstraint('available_copies >= 0', name='check_available_copies_positive'),
        CheckConstraint('available_copies <= total_copies', name='check_available_lte_total'),
    )