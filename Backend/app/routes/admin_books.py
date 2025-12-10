from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.config.database import get_db
from app.services.admin_books import add_book_with_files, add_book_without_static_content
from app.schemas.book_schemas import BookResponseSchema, BookCreateSchema, BookUpdateSchema
from app.models.books import Books
from app.services.rag_service import rag_service

router = APIRouter(prefix="/admin/books", tags=["admin-books"])


@router.get("/")
def list_all_books(db: Session = Depends(get_db)):
    """Get list of all books with their basic information and RAG indexing status"""
    books = db.query(Books).all()
    books_list = []
    
    for book in books:
        # Check RAG indexing status
        rag_status = rag_service.check_index_status(book.book_id)
        
        books_list.append({
            "book_id": book.book_id,
            "title": book.title,
            "author": book.author,
            "total_copies": book.total_copies,
            "available_copies": book.available_copies,
            "cover_image": book.cover_image,
            "pdf_url": book.pdf_url,
            "created_at": book.created_at,
            "rag_indexed": rag_status.get("indexed", False),
            "rag_collection": rag_status.get("collection_name", None)
        })
    
    return books_list


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_book(
    title: str = Form(...),
    author: str = Form(...),
    total_copies: int = Form(...),
    pdf_file: UploadFile = File(...),
    cover_image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Create a new book with full processing:
    - Uploads PDF and cover image
    - Generates summary, Q&A, podcast script, and audio (static content)
    - Indexes PDF for RAG chat (vector embeddings)
    
    This endpoint does EVERYTHING automatically.
    """
    try:
        book_data = BookCreateSchema(
            title=title,
            author=author,
            total_copies=total_copies
        )
        result = add_book_with_files(db, book_data, pdf_file, cover_image)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/quick-add", status_code=status.HTTP_201_CREATED)
def create_book_without_static_content(
    title: str = Form(...),
    author: str = Form(...),
    total_copies: int = Form(...),
    pdf_file: UploadFile = File(...),
    cover_image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Create a new book with ONLY RAG indexing (FAST):
    - Uploads PDF and cover image
    - Indexes PDF for RAG chat (vector embeddings)
    - SKIPS: summary, Q&A, podcast generation (saves time)
    
    Use this when you want faster uploads and only need the chat feature.
    Students can still use /rag/books/{book_id}/query to ask questions.
    """
    try:
        book_data = BookCreateSchema(
            title=title,
            author=author,
            total_copies=total_copies
        )
        result = add_book_without_static_content(db, book_data, pdf_file, cover_image)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{book_id}")
async def update_book(
    book_id: int,
    title: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    total_copies: Optional[int] = Form(None),
    available_copies: Optional[int] = Form(None),
    pdf_file: Optional[UploadFile] = File(None),
    cover_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Update book details. All fields are optional.
    Can update: title, author, total_copies, available_copies, PDF file, or cover image.
    """
    import os
    
    book = db.query(Books).filter(Books.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    # Update text fields
    if title is not None:
        book.title = title
    if author is not None:
        book.author = author
    
    # Handle total_copies update with constraint checking
    if total_copies is not None:
        # Calculate the new available_copies based on difference
        if book.total_copies and book.available_copies is not None:
            difference = total_copies - book.total_copies
            new_available = book.available_copies + difference
            # Ensure available_copies doesn't go negative or exceed total
            book.available_copies = max(0, min(new_available, total_copies))
        else:
            # If no previous values, set available equal to total
            book.available_copies = total_copies
        book.total_copies = total_copies
    
    # Handle available_copies update separately
    if available_copies is not None:
        # Get the current or updated total_copies
        current_total = total_copies if total_copies is not None else book.total_copies
        if available_copies > current_total:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Available copies ({available_copies}) cannot exceed total copies ({current_total})"
            )
        book.available_copies = available_copies
    
    # Update PDF file if provided
    if pdf_file and pdf_file.filename:
        try:
            # Use static/pdfs directory
            upload_dir = "static/pdfs"
            os.makedirs(upload_dir, exist_ok=True)
            pdf_filename = f"book_{book_id}_{pdf_file.filename}"
            pdf_path = os.path.join(upload_dir, pdf_filename)
            
            # Delete old PDF if exists
            if book.pdf_url and os.path.exists(book.pdf_url):
                os.remove(book.pdf_url)
            
            # Save new PDF
            with open(pdf_path, "wb") as f:
                content = await pdf_file.read()
                f.write(content)
            
            book.pdf_url = pdf_path
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading PDF: {str(e)}"
            )
    
    # Update cover image if provided
    if cover_image and cover_image.filename:
        try:
            # Use static/covers directory
            upload_dir = "static/covers"
            os.makedirs(upload_dir, exist_ok=True)
            cover_filename = f"cover_{book_id}_{cover_image.filename}"
            cover_path = os.path.join(upload_dir, cover_filename)
            
            # Delete old cover if exists
            if book.cover_image and os.path.exists(book.cover_image):
                os.remove(book.cover_image)
            
            # Save new cover
            with open(cover_path, "wb") as f:
                content = await cover_image.read()
                f.write(content)
            
            book.cover_image = cover_path
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading cover image: {str(e)}"
            )
            with open(cover_path, "wb") as f:
                content = await cover_image.read()
                f.write(content)
            
            book.cover_image = cover_path
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading cover image: {str(e)}"
            )
    
    db.commit()
    db.refresh(book)
    
    return {
        "message": "Book updated successfully",
        "book_id": book.book_id,
        "title": book.title,
        "author": book.author,
        "total_copies": book.total_copies,
        "available_copies": book.available_copies,
        "pdf_url": book.pdf_url,
        "cover_image": book.cover_image
    }


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db)
):
    """Delete a book and its RAG index"""
    book = db.query(Books).filter(Books.book_id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    # Delete RAG index first
    try:
        rag_service.delete_book_index(book_id)
    except Exception as e:
        # Continue even if RAG deletion fails (index might not exist)
        pass
    
    # Delete book record
    db.delete(book)
    db.commit()
    return
        
    
    