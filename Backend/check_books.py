"""Check book details"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT book_id, title, pdf_url FROM books WHERE book_id IN (8, 9, 10)"))
    books = result.fetchall()
    
    print("\n=== Books in Database ===\n")
    for book in books:
        book_id, title, pdf_url = book
        print(f"ID {book_id}: {title}")
        print(f"   PDF: {pdf_url}")
        print()
