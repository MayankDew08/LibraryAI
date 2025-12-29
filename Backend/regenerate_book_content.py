"""
Script to manually regenerate AI content and RAG index for a specific book
Use this when book was added but content generation failed
"""
import sys
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.books import Books
from app.services.static_content_service import create_static_content
from app.services.rag_service import rag_service
import time


def regenerate_content(book_id: int):
    """Regenerate all content for a specific book"""
    db = next(get_db())
    
    try:
        # Get book
        book = db.query(Books).filter(Books.book_id == book_id).first()
        if not book:
            print(f"❌ Book with ID {book_id} not found")
            return
        
        print(f"📚 Book: {book.title} by {book.author}")
        print(f"📄 PDF: {book.pdf_url}")
        print("\n" + "="*60)
        
        # Step 1: RAG Indexing
        print("\n🔍 Step 1: RAG Indexing...")
        try:
            rag_result = rag_service.process_pdf(book.pdf_url, book.book_id)
            if rag_result.get("success"):
                print(f"✅ RAG indexed successfully!")
                print(f"   - Pages: {rag_result.get('total_pages')}")
                print(f"   - Total chunks: {rag_result.get('total_chunks')}")
                print(f"   - Unique chunks: {rag_result.get('unique_chunks')}")
                print(f"   - Deduplication: {rag_result.get('deduplication_percentage')}%")
                
                # Update book's rag_indexed flag
                book.rag_indexed = True
                db.commit()
            else:
                print(f"❌ RAG indexing failed: {rag_result.get('error')}")
                print("   Continuing with AI content generation...")
        except Exception as e:
            print(f"❌ RAG indexing error: {str(e)}")
            print("   Continuing with AI content generation...")
        
        # Step 2: AI Content Generation
        print("\n🤖 Step 2: AI Content Generation (Summary, Q&A, Podcast)...")
        print("⏳ This may take 2-3 minutes with retry delays for rate limits...")
        print()
        
        try:
            content = create_static_content(db, book.book_id, book.pdf_url)
            print("\n✅ AI content generated successfully!")
            print(f"   - Summary: {len(content.summary_text) if content.summary_text else 0} characters")
            print(f"   - Q&A: {content.qa_json.count('question') if content.qa_json else 0} questions")
            print(f"   - Podcast: {len(content.podcast_script) if content.podcast_script else 0} characters")
            print(f"   - Audio: {'Yes' if content.podcast_audio_url else 'No'}")
            
            print("\n" + "="*60)
            print("✅ ALL CONTENT GENERATED SUCCESSFULLY!")
            print("="*60)
            
        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ AI content generation failed: {error_msg}")
            
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                print("\n⚠️  RATE LIMIT ERROR:")
                print("   Your Gemini API free tier quota is exhausted (20 requests/day)")
                print("\n📋 SOLUTIONS:")
                print("   1. Wait 24 hours for quota reset")
                print("   2. Get a paid Gemini API key with higher limits")
                print("   3. Add multiple API keys in .env for load balancing:")
                print("      GEMINI_API_KEY=key1")
                print("      GEMINI_API_KEY_2=key2")
                print("      GEMINI_API_KEY_3=key3")
                print("\n   The book is still usable for:")
                print("   - ✅ Borrowing/returning")
                print("   - ✅ RAG chat (if indexed successfully)")
                print("   - ❌ Summary, Q&A, Podcast (will be available on-demand later)")
            
            print("\n" + "="*60)
            
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python regenerate_book_content.py <book_id>")
        print("Example: python regenerate_book_content.py 7")
        sys.exit(1)
    
    try:
        book_id = int(sys.argv[1])
        regenerate_content(book_id)
    except ValueError:
        print("❌ Error: book_id must be a number")
        sys.exit(1)
