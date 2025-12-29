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

def test_get_or_create_summary():
    with patch('app.routes.student_books.get_or_generate_summary') as mock_get_or_generate_summary:
        mock_get_or_generate_summary.return_value = {
            "book_id": 1,
            "summary_text": "This is a summary.",
            "status": "exists"
        }
        
        response = client.get("/student/books/1/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == 1
        assert data["summary_text"] == "This is a summary."
        assert data["status"] == "exists"
        
def test_get_or_generate_audio():
    with patch('app.routes.student_books.get_or_generate_audio') as mock_get_or_generate_audio:
        mock_get_or_generate_audio.return_value = {
            "book_id": 1,
            "audio_url": "audio.mp3",
            "status": "exists"
        }
        
        response = client.get("/student/books/1/audio")
        
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == 1
        assert data["audio_url"] == "audio.mp3"
        assert data["status"] == "exists"