from sqlalchemy.orm import Session
from app.models.books import Books
from app.models.category import Category
import app.schemas.book_schemas as schemas_books
from app.utils.storage import save_file
from app.services.static_content_service import create_static_content
from app.services.rag_service import rag_service
from fastapi import UploadFile
from typing import List
import os


def get_or_create_categories(db: Session, category_names: List[str]) -> List[Category]:
    """
    Get existing categories or create new ones.
    Returns list of Category objects.
    """
    categories = []
    for name in category_names:
        # Check if category exists
        category = db.query(Category).filter(Category.name == name).first()
        if not category:
            # Create new category
            category = Category(name=name)
            db.add(category)
            db.flush()  # Get the ID without committing
        categories.append(category)
    return categories


def add_book_with_files(
    db: Session, 
    book_data: schemas_books.BookCreateSchema,
    pdf_file: UploadFile,
    cover_image: UploadFile
):
    """
    Add a single book with PDF and cover image.
    Automatically generates summary, Q&A, podcast script, and audio.
    """
    try:
        # Check if book already exists
        existing_book = db.query(Books).filter(
            (Books.title == book_data.title) &
            (Books.author == book_data.author)
        ).first()
        
        if existing_book:
            raise ValueError(f"Book '{book_data.title}' by '{book_data.author}' already exists.")
        
        # Validate file types
        if not pdf_file.filename.lower().endswith('.pdf'):
            raise ValueError("PDF file must have .pdf extension")
        
        allowed_image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        if not any(cover_image.filename.lower().endswith(ext) for ext in allowed_image_extensions):
            raise ValueError("Cover image must be .jpg, .jpeg, .png, or .webp")
        
        # Save PDF file
        pdf_path = save_file(pdf_file, "pdfs")
        
        # Save cover image
        cover_path = save_file(cover_image, "covers")
        
        # Create book record (PUBLIC - allows AI)
        new_book = Books(
            title=book_data.title,
            author=book_data.author,
            pdf_url=pdf_path,
            cover_image=cover_path,
            total_copies=book_data.total_copies,
            available_copies=book_data.total_copies,
            is_public=1  # Public - allows student-triggered AI generation
        )
        
        db.add(new_book)
        db.flush()  # Get book_id without committing
        
        # Handle categories
        categories = get_or_create_categories(db, book_data.categories)
        new_book.categories = categories
        
        db.commit()
        db.refresh(new_book)
        
        # Generate RAG index ONLY (no automatic AI content)
        rag_indexed = False
        rag_stats = {}
        try:
            print(f"Starting RAG indexing for book {new_book.book_id}...")
            rag_result = rag_service.process_pdf(pdf_path, new_book.book_id)
            rag_indexed = rag_result.get("success", False)
            
            if rag_indexed:
                # Update book's rag_indexed flag in database using direct query
                db.query(Books).filter(Books.book_id == new_book.book_id).update({"rag_indexed": 1})
                db.commit()
                db.refresh(new_book)
                print(f"✓ RAG indexed successfully: {rag_result.get('unique_chunks', 0)} chunks")
                rag_stats = {
                    "indexed": rag_indexed,
                    "num_chunks": rag_result.get("unique_chunks", 0),
                    "collection": rag_result.get("collection_name", "")
                }
            else:
                print(f"✗ RAG indexing failed: {rag_result.get('error', 'Unknown error')}")
                rag_stats = {"error": rag_result.get("error", "Unknown error")}
        except Exception as e:
            print(f"✗ RAG indexing exception: {str(e)}")
            rag_indexed = False
            rag_stats = {"error": str(e)}
        
        # Build success message
        if rag_indexed:
            content_message = "✓ Book added successfully with RAG indexing. Students can generate AI content on-demand and use chat feature!"
        else:
            content_message = "✓ Book added successfully. RAG indexing failed - students will need to retry or contact admin."
        
        return {
            "message": content_message,
            "book_id": new_book.book_id,
            "title": new_book.title,
            "author": new_book.author,
            "categories": [cat.name for cat in new_book.categories],
            "pdf_url": pdf_path,
            "cover_image": cover_path,
            "is_public": new_book.is_public,
            "content_generated": False,
            "rag_indexed": rag_indexed,
            "rag_stats": rag_stats,
            "note": "AI content (Summary/Q&A/Podcast) will be generated on-demand by students"
        }
            
    except Exception as e:
        db.rollback()
        # Clean up uploaded files if book creation failed
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            os.remove(pdf_path)
        if 'cover_path' in locals() and os.path.exists(cover_path):
            os.remove(cover_path)
        raise ValueError(f"Error adding book: {str(e)}")


def add_book_without_static_content(
    db: Session,
    book_data: schemas_books.BookCreateSchema,
    pdf_file: UploadFile,
    cover_image: UploadFile
):
    """
    Add a book with PDF and cover image WITHOUT generating static content.
    Only performs RAG indexing for chat functionality.
    Use this for faster book uploads when summary/Q&A/podcast not needed.
    """
    try:
        # Check if book already exists
        existing_book = db.query(Books).filter(
            (Books.title == book_data.title) &
            (Books.author == book_data.author)
        ).first()
        
        if existing_book:
            raise ValueError(f"Book '{book_data.title}' by '{book_data.author}' already exists.")
        
        # Validate file types
        if not pdf_file.filename.lower().endswith('.pdf'):
            raise ValueError("PDF file must have .pdf extension")
        
        allowed_image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        if not any(cover_image.filename.lower().endswith(ext) for ext in allowed_image_extensions):
            raise ValueError("Cover image must be .jpg, .jpeg, .png, or .webp")
        
        # Save PDF file
        pdf_path = save_file(pdf_file, "pdfs")
        
        # Save cover image
        cover_path = save_file(cover_image, "covers")
        
        # Create book record (CONFIDENTIAL - no AI)
        new_book = Books(
            title=book_data.title,
            author=book_data.author,
            pdf_url=pdf_path,
            cover_image=cover_path,
            total_copies=book_data.total_copies,
            available_copies=book_data.total_copies,
            is_public=0  # Confidential - students CANNOT generate AI content
        )
        
        db.add(new_book)
        db.flush()  # Get book_id without committing
        
        # Handle categories
        categories = get_or_create_categories(db, book_data.categories)
        new_book.categories = categories
        
        db.commit()
        db.refresh(new_book)
        
        # Generate RAG index ONLY (skip static content generation)
        rag_indexed = False
        rag_stats = {}
        message = "Book added"
        try:
            print(f"Starting RAG indexing for book {new_book.book_id}...")
            rag_result = rag_service.process_pdf(pdf_path, new_book.book_id)
            rag_indexed = rag_result.get("success", False)
            
            if rag_indexed:
                # Update book's rag_indexed flag in database using direct query
                db.query(Books).filter(Books.book_id == new_book.book_id).update({"rag_indexed": 1})
                db.commit()
                db.refresh(new_book)
                print(f"✓ RAG indexed successfully: {rag_result.get('unique_chunks', 0)} chunks")
                message = "Book added and RAG indexed successfully (confidential - students cannot generate AI content)"
                rag_stats = {
                    "indexed": rag_indexed,
                    "num_chunks": rag_result.get("unique_chunks", 0),
                    "collection": rag_result.get("collection_name", "")
                }
            else:
                print(f"✗ RAG indexing failed: {rag_result.get('error', 'Unknown error')}")
                message = f"Book added but RAG indexing failed: {rag_result.get('error', 'Unknown error')}"
                rag_stats = {"error": rag_result.get("error", "Unknown error")}
        except Exception as e:
            print(f"✗ RAG indexing exception: {str(e)}")
            rag_indexed = False
            rag_stats = {"error": str(e)}
            message = f"Book added but RAG indexing failed: {str(e)}"
        
        return {
            "message": message,
            "book_id": new_book.book_id,
            "title": new_book.title,
            "author": new_book.author,
            "categories": [cat.name for cat in new_book.categories],
            "pdf_url": pdf_path,
            "cover_image": cover_path,
            "content_generated": False,  # Explicitly False
            "rag_indexed": rag_indexed,
            "rag_stats": rag_stats,
            "note": "Static content (summary, Q&A, podcast) NOT generated. Use /rag/books/{book_id}/query for chat."
        }
    
    except Exception as e:
        db.rollback()
        # Clean up uploaded files if book creation failed
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            os.remove(pdf_path)
        if 'cover_path' in locals() and os.path.exists(cover_path):
            os.remove(cover_path)
        raise ValueError(f"Error adding book: {str(e)}")


def add_books(db: Session, books_data: list[schemas_books.BookCreateSchema]):
    """Add multiple books to the inventory (metadata only, no files)"""
    for book in books_data:
        existing_book = db.query(Books).filter(
            (Books.title == book.title) &
            (Books.author == book.author)
        ).first()
        if existing_book:
            raise ValueError(f"Book '{book.title}' by '{book.author}' already exists.")
    
    new_books = [Books(
        title=book.title,
        author=book.author,
        total_copies=book.total_copies,
        available_copies=book.total_copies
    ) for book in books_data]
    
    db.bulk_save_objects(new_books)
    db.commit()
    
    return {"message": f"{len(new_books)} books added successfully", "count": len(new_books)}