"""
Script to populate common book categories
Run this after migration to add standard categories to your database
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv(
    "SQLALCHEMY_DATABASE_URL",
    "mysql+mysqldb://root:password@localhost:3306/library_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Common book categories
COMMON_CATEGORIES = [
    "Self-Help",
    "Psychology",
    "Business",
    "Fiction",
    "Non-Fiction",
    "Biography",
    "Science",
    "Technology",
    "Philosophy",
    "History",
    "Finance",
    "Health",
    "Productivity",
    "Leadership",
    "Personal Development",
    "Marketing",
    "Economics",
    "Spirituality",
    "Education",
    "Relationships",
    "Communication",
    "Creativity",
    "Politics",
    "Sociology",
    "Literature"
]


def populate_categories():
    """Add common categories to database"""
    db = SessionLocal()
    
    try:
        print("\n📚 Populating Common Categories...")
        print("=" * 60)
        
        added = 0
        skipped = 0
        
        for category_name in COMMON_CATEGORIES:
            # Try to insert, skip if already exists
            try:
                db.execute(
                    text("INSERT INTO categories (name) VALUES (:name)"),
                    {"name": category_name}
                )
                db.commit()
                print(f"   ✅ Added: {category_name}")
                added += 1
            except Exception:
                db.rollback()
                print(f"   ⏭️  Skipped (exists): {category_name}")
                skipped += 1
        
        print("\n" + "=" * 60)
        print(f"✨ Summary:")
        print(f"   - Added: {added} categories")
        print(f"   - Skipped: {skipped} categories (already existed)")
        print(f"   - Total in database: {added + skipped} categories")
        
        # Show all categories
        print("\n📋 All categories in database:")
        result = db.execute(text("SELECT name FROM categories ORDER BY name"))
        for (name,) in result:
            print(f"   • {name}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("📚 Category Population Script")
    print("=" * 60)
    
    response = input("\nAdd common categories to database? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        populate_categories()
        print("\n✅ Categories ready to use!")
    else:
        print("\n❌ Operation cancelled.")
