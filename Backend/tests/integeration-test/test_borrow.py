import os
import sys
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, backend_path)

from fastapi.testclient import TestClient
from app.main import app
from app.config.database import get_db
from unittest.mock import patch, MagicMock
import pytest

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_dependencies():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides = {}

def test_borrow_book_success():
    with patch('app.routes.borrow.borrow_book') as mock_borrow_book:
        mock_borrow_book.return_value = {
            "borrow_id": 1,
            "user_name": "Test User",
            "user_email": "testuser@example.com",
            "book_title": "Test Book",
            "author": "Test Author",
            "borrowed_date": "2024-01-01T00:00:00",
            "due_date": "2024-01-15T00:00:00",
            "return_date": None,
            "fine_amount": 0,
            "status": "borrowed",
            "message": "Book borrowed successfully",
            "reminder": "Please return 'Test Book' by 2024-01-15 to avoid fine of Rs 5/day"
        }
        
        borrow_data = {
            "book_title": "Test Book",
            "user_email": "testuser@example.com"
        }
        
        response = client.post("/borrow/", json=borrow_data)
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Book borrowed successfully"
        assert data["book_title"] == "Test Book"
        
def test_borrow_return_without_fine():
    with patch('app.routes.borrow.student_return_book') as mock_return_book:
        mock_return_book.return_value = {
            "message": "Book returned successfully",
            "user_name": "Test User",
            "book_title": "Test Book",
            "borrowed_date": "2024-01-01T00:00:00",
            "return_date": "2024-01-10T00:00:00",
            "fine_amount": 0.0,
            "status": "returned_and_cleared"
        }
        
        return_data = {
            "book_title": "Test Book",
            "user_email": "testuser@example.com"
        }
        
        response= client.post("/borrow/student/return", json=return_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "returned_and_cleared"
        assert data["fine_amount"] == 0.0
        
def test_borrow_return_with_fine():
    with patch('app.routes.borrow.student_return_book') as mock_return_book:
        mock_return_book.return_value = {
            "message": "Book return recorded. Please pay the fine to complete the return.",
            "user_name": "Test User",
            "book_title": "Test Book",
            "borrowed_date": "2024-01-01T00:00:00",
            "due_date": "2024-01-15T00:00:00",
            "return_date": "2024-01-20T00:00:00",
            "fine_amount": 50.0,
            "days_late": 5,
            "status": "awaiting_fine_payment",
             "note": f"Please pay Rs {50.0} to admin and provide borrow_id:{1} for verification"
        }
        
        return_data = {
            "book_title": "Test Book",
            "user_email": "testuser@example.com"
        }
        
        response= client.post("/borrow/student/return", json=return_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "awaiting_fine_payment"
        assert data["fine_amount"] == 50.0