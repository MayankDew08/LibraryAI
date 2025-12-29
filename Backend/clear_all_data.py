"""
Clear all database records - Start fresh
This script will delete ALL data from all tables while preserving the schema
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


def clear_all_data():
    """Clear all records from all tables"""
    db = SessionLocal()
    
    try:
        print("\n🗑️  Clearing all database records...")
        print("=" * 60)
        
        # Disable foreign key checks temporarily
        print("\n1️⃣ Disabling foreign key checks...")
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        db.commit()
        
        # Get all table names
        result = db.execute(text("""
            SELECT TABLE_NAME 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_TYPE = 'BASE TABLE'
        """))
        
        tables = [row[0] for row in result]
        
        print(f"\n2️⃣ Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table}")
        
        # Truncate all tables
        print(f"\n3️⃣ Truncating all tables...")
        for table in tables:
            try:
                db.execute(text(f"TRUNCATE TABLE {table}"))
                print(f"   ✅ Cleared: {table}")
            except Exception as e:
                print(f"   ⚠️  Error clearing {table}: {str(e)}")
        
        db.commit()
        
        # Re-enable foreign key checks
        print("\n4️⃣ Re-enabling foreign key checks...")
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        db.commit()
        
        # Verify all tables are empty
        print("\n5️⃣ Verifying data cleared...")
        all_empty = True
        for table in tables:
            count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
            if count > 0:
                print(f"   ⚠️  {table} still has {count} records")
                all_empty = False
            else:
                print(f"   ✅ {table}: 0 records")
        
        if all_empty:
            print("\n✨ All database records cleared successfully!")
            print("\n📊 Summary:")
            print(f"   - Tables cleared: {len(tables)}")
            print(f"   - Schema preserved: Yes")
            print(f"   - Ready for fresh data: Yes")
        else:
            print("\n⚠️  Some tables still have data. Check errors above.")
        
        # Also clear vector database if it exists
        print("\n6️⃣ Checking vector database...")
        vectordb_path = os.path.join(os.path.dirname(__file__), "static", "vectordb")
        if os.path.exists(vectordb_path):
            import shutil
            try:
                shutil.rmtree(vectordb_path)
                os.makedirs(vectordb_path, exist_ok=True)
                print("   ✅ Vector database cleared")
            except Exception as e:
                print(f"   ⚠️  Error clearing vector DB: {str(e)}")
        else:
            print("   ℹ️  No vector database found")
        
        # Clear uploaded files
        print("\n7️⃣ Checking uploaded files...")
        static_path = os.path.join(os.path.dirname(__file__), "static")
        
        folders_to_clear = ["pdfs", "covers", "podcasts"]
        for folder in folders_to_clear:
            folder_path = os.path.join(static_path, folder)
            if os.path.exists(folder_path):
                import shutil
                try:
                    shutil.rmtree(folder_path)
                    os.makedirs(folder_path, exist_ok=True)
                    print(f"   ✅ Cleared: {folder}/")
                except Exception as e:
                    print(f"   ⚠️  Error clearing {folder}: {str(e)}")
            else:
                os.makedirs(folder_path, exist_ok=True)
                print(f"   ℹ️  Created: {folder}/")
        
        print("\n" + "=" * 60)
        print("🎉 Database is now clean and ready for fresh data!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error clearing data: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🗑️  CLEAR ALL DATABASE RECORDS")
    print("=" * 60)
    
    print("\n⚠️  WARNING: This will delete ALL data from your database!")
    print("   - All books will be removed")
    print("   - All users will be removed")
    print("   - All borrow records will be removed")
    print("   - All categories will be removed")
    print("   - All uploaded files will be deleted")
    print("   - All vector database data will be deleted")
    print("\n   Schema and tables will be preserved.")
    
    response = input("\n❓ Are you sure you want to continue? Type 'YES' to confirm: ")
    
    if response == "YES":
        clear_all_data()
        print("\n✅ You can now add fresh data to your system!")
        print("   Consider running: python populate_categories.py")
    else:
        print("\n❌ Operation cancelled. Database unchanged.")
