"""
Quick test to verify category system is working
Run this AFTER migration to validate the setup
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.books import Books
from app.models.category import Category
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv(
    "SQLALCHEMY_DATABASE_URL",
    "mysql+mysqldb://root:password@localhost:3306/library_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def test_category_system():
    """Test category relationships"""
    db = SessionLocal()
    
    try:
        print("\n🧪 Testing Category System...")
        print("=" * 60)
        
        # Test 1: Check tables exist
        print("\n1️⃣ Checking tables...")
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = ['books', 'categories', 'book_categories']
        for table in required_tables:
            if table in tables:
                print(f"   ✅ {table} exists")
            else:
                print(f"   ❌ {table} NOT FOUND")
                return
        
        # Test 2: Check Books model relationships
        print("\n2️⃣ Testing Books model...")
        books = db.query(Books).all()
        print(f"   Found {len(books)} books")
        
        if books:
            book = books[0]
            print(f"   Sample book: {book.title}")
            print(f"   Categories: {[cat.name for cat in book.categories]}")
        
        # Test 3: Check Categories
        print("\n3️⃣ Testing Categories...")
        categories = db.query(Category).all()
        print(f"   Found {len(categories)} categories:")
        for cat in categories:
            book_count = len(cat.books)
            print(f"      - {cat.name} ({book_count} books)")
        
        # Test 4: Test search functionality
        print("\n4️⃣ Testing search (if books exist)...")
        if books:
            from app.services.student_books import search_books
            
            # Search by title
            title_results = search_books(db, title="a")
            print(f"   Search by title 'a': {len(title_results)} results")
            
            # Search by category (if categories exist)
            if categories:
                cat_results = search_books(db, categories=[categories[0].name])
                print(f"   Search by category '{categories[0].name}': {len(cat_results)} results")
        
        print("\n✅ All tests passed!")
        print("\n📊 Summary:")
        print(f"   - Books: {len(books)}")
        print(f"   - Categories: {len(categories)}")
        print(f"   - System ready for use!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_category_system()
