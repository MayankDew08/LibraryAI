"""
RAG Endpoints for Library Management System
Handles document Q&A and chat functionality
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.books import Books
from app.services.rag_service import rag_service
from pydantic import BaseModel
from typing import Optional
import time 
import logging
import os
import datetime

router = APIRouter(prefix="/rag", tags=["RAG"])

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(lineno)d - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger=logging.getLogger('profiler')
    


class QueryRequest(BaseModel):
    """Request schema for querying a book"""
    question: str
    num_chunks: Optional[int] = 5  # Number of chunks to retrieve


class QueryResponse(BaseModel):
    """Response schema for book queries"""
    book_title: str
    question: str
    answer: str
    sources: list
    chunks_used: int


@router.post("/books/{book_id}/query")
async def query_book(
    book_id: int,
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Ask a question about a specific book using RAG
    
    - Retrieves relevant chunks using MMR (Maximal Marginal Relevance)
    - Generates comprehensive answer combining book content + general knowledge
    - Returns answer with source citations (page numbers + previews)
    
    **Example:**
    ```json
    {
        "question": "What is database normalization?",
        "num_chunks": 5
    }
    ```
    """
    # Phase 1: Database verification
    db_start = time.time()
    book = db.query(Books).filter(Books.book_id == book_id).first()
    db_time = time.time() - db_start
    
    if not book:
        logger.warning(f"Book {book_id} not found - db_time={db_time:.4f}s")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    # Phase 2: RAG query
    rag_start = time.time()
    num_chunks = request.num_chunks if request.num_chunks is not None else 5
    result = await rag_service.query_book(book_id, request.question, num_chunks)
    rag_time = time.time() - rag_start
    
    if not result["success"]:
        logger.error(f"RAG query failed for book {book_id} - db_time={db_time:.4f}s rag_time={rag_time:.4f}s error={result['error']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"]
        )
    
    # Phase 3: Response formatting
    format_start = time.time()
    response_data = {
        "book_id": book_id,
        "book_title": book.title,
        "author": book.author,
        "question": result["question"],
        "answer": result["answer"],
        "sources": result["sources"],
        "chunks_used": result["num_chunks_used"],
        "message": "Query successful - answer generated using RAG"
    }
    format_time = time.time() - format_start
    
    # Log detailed profiling
    total_time = db_time + rag_time + format_time
    logger.info(f"RAG Query Profile - Book {book_id}: db={db_time:.4f}s rag={rag_time:.4f}s format={format_time:.4f}s total={total_time:.4f}s cache_hit={result.get('cached', False)}")
    
    return response_data


@router.get("/books/{book_id}/index-status")
def get_index_status(book_id: int, db: Session = Depends(get_db)):
    """
    Check if a book has been indexed in the vector database
    
    Returns:
    - indexed: True if book is indexed
    - collection_name: Name of the ChromaDB collection
    - book_info: Basic book details
    """
    # Verify book exists
    book = db.query(Books).filter(Books.book_id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    # Check if vectorstore exists
    import os
    collection_name = f"book_{book_id}"
    vectorstore_path = os.path.join("static/vectordb", collection_name)
    
    indexed = os.path.exists(vectorstore_path)
    
    return {
        "book_id": book_id,
        "book_title": book.title,
        "indexed": indexed,
        "collection_name": collection_name,
        "has_pdf": book.pdf_file_path is not None,
        "pdf_path": book.pdf_file_path
    }


@router.post("/books/{book_id}/reindex")
def reindex_book(book_id: int, db: Session = Depends(get_db)):
    """
    Re-index a book (useful if PDF was updated or indexing failed)
    
    - Deletes old index
    - Re-processes PDF
    - Creates new vector embeddings
    """
    # Verify book exists
    book = db.query(Books).filter(Books.book_id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    if not book.pdf_file_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book has no PDF file to index"
        )
    
    # Delete old index if exists
    rag_service.delete_book_index(book_id)
    
    # Re-process PDF
    result = rag_service.process_pdf(book.pdf_file_path, book_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"]
        )
    
    return {
        "message": "Book re-indexed successfully",
        "book_id": book_id,
        "book_title": book.title,
        "stats": {
            "total_pages": result["total_pages"],
            "total_chunks": result["total_chunks"],
            "unique_chunks": result["unique_chunks"],
            "deduplication": f"{result['deduplication_percentage']}%",
            "collection_name": result["collection_name"]
        }
    }


@router.delete("/books/{book_id}/index")
async def delete_book_index(book_id: int, db: Session = Depends(get_db)):
    """
    Delete vector index for a book (cleanup when book is deleted)
    
    - Admin only
    - Removes all embeddings and chunks from vector database
    """
    # Verify book exists
    book = db.query(Books).filter(Books.book_id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    # Delete index (now async)
    result = await rag_service.delete_book_index(book_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["error"]
        )
    
    return {
        "message": f"Vector index deleted for book '{book.title}'",
        "book_id": book_id
    }
