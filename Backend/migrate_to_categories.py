"""
Database migration script to add category support
Run this script ONCE to migrate from single category column to many-to-many relationship

Steps:
1. Creates 'categories' table
2. Creates 'book_categories' junction table
3. Migrates existing category data from books table
4. Drops the old category column from books table

Usage:
    conda activate audiolib
    python migrate_to_categories.py
"""

from sqlalchemy import create_engine, Column, Integer, String, Table, ForeignKey, text
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
import os

load_dotenv()

# Get database URL
DATABASE_URL = os.getenv(
    "SQLALCHEMY_DATABASE_URL",
    "mysql+mysqldb://root:password@localhost:3306/library_db"
)

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def migrate_categories():
    """Perform the migration"""
    db = SessionLocal()
    
    try:
        print("\n🚀 Starting category migration...")
        
        # Step 1: Create categories table
        print("\n1️⃣ Creating 'categories' table...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS categories (
                category_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                INDEX idx_category_name (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        db.commit()
        print("   ✅ Categories table created")
        
        # Step 2: Create book_categories junction table
        print("\n2️⃣ Creating 'book_categories' junction table...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS book_categories (
                book_id INT NOT NULL,
                category_id INT NOT NULL,
                PRIMARY KEY (book_id, category_id),
                FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE,
                INDEX idx_book_categories_book (book_id),
                INDEX idx_book_categories_category (category_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        db.commit()
        print("   ✅ Book-categories junction table created")
        
        # Step 3: Check if category column exists in books table
        print("\n3️⃣ Checking for existing category data...")
        result = db.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'books' 
            AND COLUMN_NAME = 'category'
        """)).fetchone()
        
        has_category_column = result[0] > 0
        
        if has_category_column:
            print("   ℹ️ Found existing category column - migrating data...")
            
            # Get all unique categories from books table
            existing_categories = db.execute(text("""
                SELECT DISTINCT category 
                FROM books 
                WHERE category IS NOT NULL AND category != ''
            """)).fetchall()
            
            # Insert categories into categories table
            category_map = {}
            for (cat_name,) in existing_categories:
                if cat_name:
                    result = db.execute(
                        text("INSERT INTO categories (name) VALUES (:name) ON DUPLICATE KEY UPDATE category_id=LAST_INSERT_ID(category_id)"),
                        {"name": cat_name}
                    )
                    db.commit()
                    
                    # Get the category_id
                    cat_id = db.execute(
                        text("SELECT category_id FROM categories WHERE name = :name"),
                        {"name": cat_name}
                    ).fetchone()[0]
                    
                    category_map[cat_name] = cat_id
            
            print(f"   ✅ Migrated {len(category_map)} unique categories")
            
            # Migrate book-category relationships
            print("\n4️⃣ Migrating book-category relationships...")
            books = db.execute(text("""
                SELECT book_id, category 
                FROM books 
                WHERE category IS NOT NULL AND category != ''
            """)).fetchall()
            
            migrated_count = 0
            for book_id, category in books:
                if category in category_map:
                    db.execute(
                        text("INSERT IGNORE INTO book_categories (book_id, category_id) VALUES (:book_id, :category_id)"),
                        {"book_id": book_id, "category_id": category_map[category]}
                    )
                    migrated_count += 1
            
            db.commit()
            print(f"   ✅ Migrated {migrated_count} book-category relationships")
            
            # Step 5: Drop old category column
            print("\n5️⃣ Dropping old 'category' column from books table...")
            db.execute(text("ALTER TABLE books DROP COLUMN category"))
            db.commit()
            print("   ✅ Old category column dropped")
            
        else:
            print("   ℹ️ No category column found - fresh installation")
        
        # Step 6: Update title and author to NOT NULL if they are nullable
        print("\n6️⃣ Ensuring title and author are NOT NULL...")
        db.execute(text("""
            ALTER TABLE books 
            MODIFY COLUMN title VARCHAR(255) NOT NULL,
            MODIFY COLUMN author VARCHAR(255) NOT NULL
        """))
        db.commit()
        print("   ✅ Title and author columns updated")
        
        print("\n✨ Migration completed successfully!")
        print("\n📊 Summary:")
        
        # Show statistics
        category_count = db.execute(text("SELECT COUNT(*) FROM categories")).fetchone()[0]
        book_count = db.execute(text("SELECT COUNT(*) FROM books")).fetchone()[0]
        relationship_count = db.execute(text("SELECT COUNT(*) FROM book_categories")).fetchone()[0]
        
        print(f"   - Total categories: {category_count}")
        print(f"   - Total books: {book_count}")
        print(f"   - Total book-category relationships: {relationship_count}")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("📚 Library Management System - Category Migration")
    print("=" * 60)
    
    response = input("\n⚠️  This will modify your database schema. Continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        migrate_categories()
        print("\n✅ You can now restart your FastAPI server!")
        print("   The category system is ready to use.\n")
    else:
        print("\n❌ Migration cancelled.")
