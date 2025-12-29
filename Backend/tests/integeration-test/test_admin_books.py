import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi.testclient import TestClient
from app.main import app
from app.config.database import get_db
from app.services.auth import get_current_admin
from unittest.mock import patch, MagicMock
import pytest

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_dependencies():
    mock_db = MagicMock()
    mock_admin = MagicMock()
    
    # Mock the database query
    mock_books = []
    mock_db.query().all.return_value = mock_books
    
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_admin] = lambda: mock_admin
    
    yield
    
    app.dependency_overrides = {}

def test_list_all_books():
    # Set up mock books
    mock_book1 = MagicMock()
    mock_book1.book_id = 1
    mock_book1.title = "Book One"
    mock_book1.author = "Author A"
    mock_book1.categories = [MagicMock(name="Fiction"), MagicMock(name="Adventure")]
    mock_book1.total_copies = 5
    mock_book1.available_copies = 3
    mock_book1.cover_image = "cover1.jpg"
    mock_book1.pdf_url = "book1.pdf"
    mock_book1.created_at = "2024-01-01"
    mock_book1.is_public = True
    mock_book1.rag_indexed = True

    mock_book2 = MagicMock()
    mock_book2.book_id = 2
    mock_book2.title = "Book Two"
    mock_book2.author = "Author B"
    mock_book2.categories = [MagicMock(name="Non-Fiction")]
    mock_book2.total_copies = 10
    mock_book2.available_copies = 7
    mock_book2.cover_image = "cover2.jpg"
    mock_book2.pdf_url = "book2.pdf"
    mock_book2.created_at = "2024-02-01"
    mock_book2.is_public = False
    mock_book2.rag_indexed = True

    # Get the mock db from overrides
    mock_db = app.dependency_overrides[get_db]()
    mock_db.query().all.return_value = [mock_book1, mock_book2]

    response = client.get("/admin/books/")

    assert response.status_code == 200
    books_list = response.json()
    assert len(books_list) == 2
    assert books_list[0]["title"] == "Book One"
    assert books_list[1]["title"] == "Book Two"
    
def test_create_book():
    with patch("app.routes.admin_books.add_book_with_files") as mock_add_book:
        mock_add_book.return_value = {
            "message": "Book added successfully",
            "book_id": 1,
            "title": "New Book",
            "author": "New Author",
            "categories": ["Fiction", "Adventure"],
            "pdf_url": "new_book.pdf",
            "cover_image": "new_cover.jpg",
            "is_public": True,
            "content_generated": False,
            "rag_indexed": True,
            "rag_status": "✓ Book added successfully with RAG indexing. Students can generate AI content on-demand and use chat feature!",
            "note": "AI content (Summary/Q&A/Podcast) will be generated on-demand by students"
        }
        
        files = {
            "pdf_file": ("new_book.pdf", b"PDF file content", "application/pdf"),
            "cover_image": ("new_cover.jpg", b"Image file content", "image/jpeg")
        }
        data = {
            "title": "New Book",
            "author": "New Author",
            "total_copies": 5,
            "categories": "Fiction,Adventure"
        }
        
        response = client.post("/admin/books/", data=data, files=files)
        
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["message"] == "Book added successfully"
        assert response_data["title"] == "New Book"
        assert response_data["author"] == "New Author"
        
def test_delete_book():
    with patch("app.routes.admin_books.rag_service.delete_book_index") as mock_delete_index:
        mock_delete_index.return_value = None
        
        # Get the mock db
        mock_db = app.dependency_overrides[get_db]()
        
        # Mock the book
        mock_book = MagicMock()
        mock_book.book_id = 1
        mock_book.title = "Book to Delete"
        
        mock_db.query().filter().first.return_value = mock_book
        
        response = client.delete("/admin/books/1")
        
        assert response.status_code == 204
        mock_delete_index.assert_called_once_with(1)
        mock_db.delete.assert_called_once_with(mock_book)
        mock_db.commit.assert_called_once()
    