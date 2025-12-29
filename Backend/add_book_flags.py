"""
Add is_public and rag_indexed columns to books table
Run this once to update existing database
"""
from sqlalchemy import create_engine, text
from app.config.settings import DATABASE_URL

engine = create_engine(DATABASE_URL)

print("Adding is_public and rag_indexed columns to books table...")

with engine.connect() as conn:
    try:
        # Add is_public column (default 1 = public)
        conn.execute(text("""
            ALTER TABLE books 
            ADD COLUMN is_public INTEGER NOT NULL DEFAULT 1
        """))
        print("✓ Added is_public column")
    except Exception as e:
        if "Duplicate column" in str(e) or "already exists" in str(e):
            print("ℹ is_public column already exists")
        else:
            print(f"✗ Error adding is_public: {e}")
    
    try:
        # Add rag_indexed column (default 0 = not indexed)
        conn.execute(text("""
            ALTER TABLE books 
            ADD COLUMN rag_indexed INTEGER NOT NULL DEFAULT 0
        """))
        print("✓ Added rag_indexed column")
    except Exception as e:
        if "Duplicate column" in str(e) or "already exists" in str(e):
            print("ℹ rag_indexed column already exists")
        else:
            print(f"✗ Error adding rag_indexed: {e}")
    
    conn.commit()
    print("\n✓ Migration complete!")
