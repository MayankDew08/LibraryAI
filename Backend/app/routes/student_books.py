from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.schemas.static_content_schemas import StaticContentSchema
from app.services.student_books import (
    get_static_content, 
    search_books,
    get_or_generate_summary,
    get_or_generate_qa,
    get_or_generate_audio
)
from app.config.database import get_db
from typing import List

router = APIRouter(prefix="/student/books", tags=["student-books"])


@router.get("/")
def list_all_books(db: Session = Depends(get_db)):
    """Get list of all available books for students"""
    from app.models.books import Books
    books = db.query(Books).all()
    return [
        {
            "book_id": book.book_id,
            "title": book.title,
            "author": book.author,
            "available_copies": book.available_copies,
            "total_copies": book.total_copies,
            "cover_image": book.cover_image,
            "pdf_url": book.pdf_url
        }
        for book in books
    ]


@router.get("/search")
def search_books_by_title(
    title: str = Query(..., min_length=1, description="Book title to search for"),
    db: Session = Depends(get_db)
):
    """Search for books by title (case-insensitive partial match)"""
    try:
        books = search_books(db, title)
        return books
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{book_id}/summary")
def get_book_summary(book_id: int, db: Session = Depends(get_db)):
    """
    Get or generate summary for a specific book.
    Generates on-demand if it doesn't exist yet.
    """
    try:
        result = get_or_generate_summary(db, book_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


@router.get("/{book_id}/qa")
def get_book_qa(book_id: int, db: Session = Depends(get_db)):
    """
    Get or generate Q&A pairs for a specific book.
    Generates on-demand if it doesn't exist yet.
    """
    try:
        result = get_or_generate_qa(db, book_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating Q&A: {str(e)}")


@router.get("/{book_id}/audio")
def get_book_audio(book_id: int, db: Session = Depends(get_db)):
    """
    Get or generate audio file for a specific book.
    Generates on-demand if it doesn't exist yet.
    Requires podcast script to be generated first.
    """
    try:
        result = get_or_generate_audio(db, book_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating audio: {str(e)}")


@router.get("/{book_id}/static-content", response_model=StaticContentSchema)
def read_static_content(book_id: int, db: Session = Depends(get_db)):
    """
    Endpoint for students to retrieve all static content for a specific book.
    Returns existing content without generating anything new.
    Use individual endpoints (/summary, /qa, /audio) for on-demand generation.
    """
    try:
        content = get_static_content(db, book_id)
        return content
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))