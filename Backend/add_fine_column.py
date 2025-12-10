"""
Script to add fine_amount column to borrow_records table
"""
import MySQLdb
from app.config.database import SQLALCHEMY_DATABASE_URL
import re

# Parse database URL
pattern = r'mysql\+mysqldb://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
match = re.match(pattern, SQLALCHEMY_DATABASE_URL)

if not match:
    print("Error: Could not parse database URL")
    exit(1)

user, password, host, port, database = match.groups()

print(f"Connecting to database: {database}@{host}")

try:
    # Connect to MySQL
    conn = MySQLdb.connect(
        host=host,
        user=user,
        passwd=password,
        db=database,
        port=int(port)
    )
    cursor = conn.cursor()
    
    print("\n✅ Connected to database successfully!")
    
    # Add fine_amount column if it doesn't exist
    try:
        print("\nAdding fine_amount column...")
        cursor.execute("""
            ALTER TABLE borrow_records 
            ADD COLUMN fine_amount FLOAT DEFAULT 0.0 NOT NULL AFTER return_date
        """)
        conn.commit()
        print("✅ fine_amount column added successfully!")
    except MySQLdb.Error as e:
        if "Duplicate column name" in str(e):
            print("ℹ️  fine_amount column already exists")
        else:
            raise
    
    # Verify the changes
    print("\n📊 Verifying borrow_records structure:")
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = 'borrow_records'
        ORDER BY ORDINAL_POSITION
    """, (database,))
    
    results = cursor.fetchall()
    for column_name, data_type, is_nullable, default_value in results:
        nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
        default = f"DEFAULT {default_value}" if default_value else ""
        print(f"  {column_name}: {data_type} {nullable} {default}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Database update complete!")

except MySQLdb.Error as e:
    print(f"\n❌ Error: {e}")
    exit(1)
