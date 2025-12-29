"""
Create admins table for separate admin authentication
Run this script to add the admins table to your database
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


def create_admins_table():
    """Create admins table"""
    db = SessionLocal()
    
    try:
        print("\n📊 Creating admins table...")
        print("=" * 60)
        
        # Create admins table
        print("\n1️⃣ Creating 'admins' table...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS admins (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                is_active INT NOT NULL DEFAULT 1,
                INDEX idx_admin_name (name),
                INDEX idx_admin_email (email)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        db.commit()
        print("   ✅ Admins table created")
        
        # Check if table was created
        result = db.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'admins'
        """)).fetchone()
        
        if result[0] > 0:
            print("\n✨ Admins table created successfully!")
            print("\n📋 Table Structure:")
            print("   - id (Primary Key)")
            print("   - name")
            print("   - email (Unique)")
            print("   - hashed_password")
            print("   - created_at")
            print("   - updated_at")
            print("   - is_active")
            
            # Get count
            count = db.execute(text("SELECT COUNT(*) FROM admins")).fetchone()[0]
            print(f"\n📊 Current admin count: {count}")
            
            print("\n✅ Ready to register admins via POST /auth/admin/register")
        else:
            print("\n⚠️  Table creation might have failed")
        
    except Exception as e:
        print(f"\n❌ Error creating table: {str(e)}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("📊 Create Admins Table")
    print("=" * 60)
    
    response = input("\nCreate admins table? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        create_admins_table()
        print("\n✅ Admins table ready!")
        print("   Now you can:")
        print("   1. Register admin via POST /auth/admin/register")
        print("   2. Login via POST /auth/admin/login (with OTP)")
    else:
        print("\n❌ Operation cancelled.")
