"""
Service for generating and saving static content for books
"""
from sqlalchemy.orm import Session
from app.models.static_content import StaticContent
from app.services.gemini_ai import generate_all_content
from app.services.audio_generation import generate_podcast_audio
import os
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)


def create_static_content(db: Session, book_id: int, pdf_path: str) -> StaticContent:
    """
    Generate all static content (summary, Q&A, podcast script, audio) for a book
    """
    try:
        # Check if content already exists
        existing_content = db.query(StaticContent).filter(
            StaticContent.book_id == book_id
        ).first()
        
        if existing_content:
            raise ValueError(f"Static content already exists for book ID {book_id}")
        
        # Generate content using Gemini AI
        content_data = generate_all_content(pdf_path)
        
        # Generate podcast audio from script
        audio_url = generate_podcast_audio(
            content_data["podcast_script"], 
            book_id
        )
        
        # Create static content record
        new_content = StaticContent(
            book_id=book_id,
            summary_text=content_data["summary_text"],
            qa_json=content_data["qa_json"],
            podcast_script=content_data["podcast_script"],
            audio_url=audio_url
        )
        
        db.commit()
        db.refresh(new_content)
        
        # Invalidate cache for this book's static content
        summary_cache_key = f"summary_{book_id}"
        qa_cache_key = f"qa_{book_id}"
        podcast_cache_key = f"podcast_{book_id}"
        audio_cache_key = f"audio_url_{book_id}"
        redis_client.delete(summary_cache_key)
        redis_client.delete(qa_cache_key)
        redis_client.delete(podcast_cache_key)
        redis_client.delete(audio_cache_key)
        
        return new_content
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error creating static content: {str(e)}")


def regenerate_static_content(db: Session, book_id: int, pdf_path: str) -> StaticContent:
    """
    Regenerate static content for an existing book
    """
    try:
        # Get existing content
        content = db.query(StaticContent).filter(
            StaticContent.book_id == book_id
        ).first()
        
        if not content:
            raise ValueError(f"No static content found for book ID {book_id}")
        
        # Delete old audio file if exists
        if content.audio_url and os.path.exists(content.audio_url):
            os.remove(content.audio_url)
        
        # Generate new content
        content_data = generate_all_content(pdf_path)
        
        # Generate new podcast audio
        audio_url = generate_podcast_audio(
            content_data["podcast_script"], 
            book_id
        )
        
        # Update content
        content.summary_text = content_data["summary_text"]
        content.qa_json = content_data["qa_json"]
        content.podcast_script = content_data["podcast_script"]
        content.audio_url = audio_url
        
        db.commit()
        db.refresh(content)
        
        # Invalidate cache for this book's static content
        summary_cache_key = f"summary_{book_id}"
        qa_cache_key = f"qa_{book_id}"
        podcast_cache_key = f"podcast_{book_id}"
        audio_cache_key = f"audio_url_{book_id}"
        redis_client.delete(summary_cache_key)
        redis_client.delete(qa_cache_key)
        redis_client.delete(podcast_cache_key)
        redis_client.delete(audio_cache_key)
        
        return content
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error regenerating static content: {str(e)}")
