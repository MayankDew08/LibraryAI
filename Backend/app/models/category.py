from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.config.database import Base

# Junction table for many-to-many relationship between Books and Categories
book_categories = Table(
    'book_categories',
    Base.metadata,
    Column('book_id', Integer, ForeignKey('books.book_id', ondelete='CASCADE'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.category_id', ondelete='CASCADE'), primary_key=True)
)


class Category(Base):
    """Category model for book classification"""
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    
    # Relationship to books (many-to-many)
    books = relationship("Books", secondary=book_categories, back_populates="categories")
