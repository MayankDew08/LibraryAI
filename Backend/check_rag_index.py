"""Check if books are indexed in RAG system"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import rag_service
from sqlalchemy import create_engine, text
from app.config.settings import settings

# Create database connection
engine = create_engine(settings.DATABASE_URL)

# Get all books
with engine.connect() as conn:
    result = conn.execute(text("SELECT book_id, title, pdf_url FROM books"))
    books = result.fetchall()
    
    print("\n=== Books and RAG Index Status ===\n")
    
    for book in books:
        book_id, title, pdf_url = book
        print(f"Book ID: {book_id}")
        print(f"Title: {title}")
        print(f"PDF: {pdf_url}")
        
        # Check if indexed
        status = rag_service.check_index_status(book_id)
        if status["indexed"]:
            print(f"✅ RAG Indexed: YES")
            print(f"   Collection: {status['collection_name']}")
        else:
            print(f"❌ RAG Indexed: NO")
            print(f"   Message: {status.get('message', 'Not indexed')}")
        
        print("-" * 60)
