from sqlalchemy.orm import Session
from app.models.static_content import StaticContent
from app.models.books import Books
import app.schemas.static_content_schemas as schemas_static_content
from app.services.gemini_ai import generate_summary, generate_qa_pairs, generate_podcast_script
from app.services.audio_generation import generate_podcast_audio
import os
from typing import Dict, Any


def search_books(db: Session, title: str):
    """
    Search for books by title (case-insensitive partial match)
    
    Args:
        db: Database session
        title: Book title to search for
        
    Returns:
        List of matching books with basic info
    """
    if not title or len(title.strip()) < 1:
        raise ValueError("Search title must be at least 1 character")
    
    # Case-insensitive partial match search
    books = db.query(Books).filter(
        Books.title.ilike(f"%{title}%")
    ).all()
    
    # Return formatted results
    return [
        {
            "book_id": book.book_id,
            "title": book.title,
            "author": book.author,
            "cover_image": book.cover_image,
            "available_copies": book.available_copies,
            "total_copies": book.total_copies
        }
        for book in books
    ]


def get_or_generate_summary(db: Session, book_id: int) -> Dict[str, Any]:
    """Get summary for a book (read-only for students)"""
    # Check if book exists
    book = db.query(Books).filter(Books.book_id == book_id).first()
    if not book:
        raise ValueError(f"Book with ID {book_id} not found")
    
    # Get content record (don't create if doesn't exist)
    content = db.query(StaticContent).filter(StaticContent.book_id == book_id).first()
    
    if not content or content.summary_text is None or str(content.summary_text).strip() == "":
        raise ValueError(f"Summary not available for book {book_id}. Please contact admin to generate static content.")
    
    return {
        "book_id": book_id,
        "summary_text": str(content.summary_text),
        "status": "exists"
    }


def get_or_generate_qa(db: Session, book_id: int) -> Dict[str, Any]:
    """Get Q&A pairs for a book (read-only for students)"""
    # Check if book exists
    book = db.query(Books).filter(Books.book_id == book_id).first()
    if not book:
        raise ValueError(f"Book with ID {book_id} not found")
    
    # Get content record (don't create if doesn't exist)
    content = db.query(StaticContent).filter(StaticContent.book_id == book_id).first()
    
    if not content or content.qa_json is None or str(content.qa_json).strip() == "":
        raise ValueError(f"Q&A not available for book {book_id}. Please contact admin to generate static content.")
    
    return {
        "book_id": book_id,
        "qa_json": str(content.qa_json),
        "status": "exists"
    }


def get_or_generate_podcast(db: Session, book_id: int) -> Dict[str, Any]:
    """Get or generate podcast script for a book"""
    # Check if book exists
    book = db.query(Books).filter(Books.book_id == book_id).first()
    if not book:
        raise ValueError(f"Book with ID {book_id} not found")
    
    pdf_url = str(book.pdf_url) if book.pdf_url is not None else None
    if pdf_url is None:
        raise ValueError(f"Book {book_id} has no PDF file")
    
    # Get or create content record
    content = db.query(StaticContent).filter(StaticContent.book_id == book_id).first()
    
    if not content:
        # Create new content record
        content = StaticContent(book_id=book_id)
        db.add(content)
        db.commit()
        db.refresh(content)
    
    # If podcast doesn't exist, generate it
    podcast_exists = content.podcast_script is not None and str(content.podcast_script).strip() != ""
    if not podcast_exists:
        podcast_script = generate_podcast_script(pdf_url)
        content.podcast_script = podcast_script  # type: ignore
        db.commit()
        db.refresh(content)
        status = "generated"
    else:
        status = "exists"
    
    return {
        "book_id": book_id,
        "podcast_script": str(content.podcast_script) if content.podcast_script is not None else None,
        "status": status
    }


def get_or_generate_audio(db: Session, book_id: int) -> Dict[str, Any]:
    """Get audio file for a book (read-only for students)"""
    # Check if book exists
    book = db.query(Books).filter(Books.book_id == book_id).first()
    if not book:
        raise ValueError(f"Book with ID {book_id} not found")
    
    # Get content record (don't create if doesn't exist)
    content = db.query(StaticContent).filter(StaticContent.book_id == book_id).first()
    
    if not content or content.audio_url is None or str(content.audio_url).strip() == "":
        raise ValueError(f"Audio not available for book {book_id}. Please contact admin to generate static content.")
    
    return {
        "book_id": book_id,
        "audio_url": str(content.audio_url),
        "status": "exists"
    }


def get_static_content(db: Session, book_id: int):
    """Retrieve all static content for a specific book (without generating)"""
    content = db.query(StaticContent).filter(StaticContent.book_id == book_id).first()
    
    if not content:
        raise ValueError(f"No content found for book {book_id}. Use individual endpoints to generate content.")
    
    # Build response with pdf_url from the book relationship
    response_data = {
        "content_id": content.content_id,
        "book_id": content.book_id,
        "pdf_url": content.book.pdf_url if content.book else None,
        "summary_text": content.summary_text,
        "qa_json": content.qa_json,
        "podcast_script": content.podcast_script,
        "audio_url": content.audio_url,
        "created_at": content.created_at,
        "updated_at": content.updated_at
    }
    
    return schemas_static_content.StaticContentSchema(**response_data)
