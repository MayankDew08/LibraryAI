"""
Script to remove notes column from borrow_records table
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
    
    # Remove notes, reissue_count, and last_reissue_date columns
    try:
        print("\nRemoving notes column...")
        cursor.execute("ALTER TABLE borrow_records DROP COLUMN notes")
        conn.commit()
        print("✅ notes column removed successfully!")
    except MySQLdb.Error as e:
        if "Can't DROP" in str(e):
            print("ℹ️  notes column doesn't exist")
        else:
            raise
    
    try:
        print("\nRemoving reissue_count column...")
        cursor.execute("ALTER TABLE borrow_records DROP COLUMN reissue_count")
        conn.commit()
        print("✅ reissue_count column removed successfully!")
    except MySQLdb.Error as e:
        if "Can't DROP" in str(e):
            print("ℹ️  reissue_count column doesn't exist")
        else:
            raise
    
    try:
        print("\nRemoving last_reissue_date column...")
        cursor.execute("ALTER TABLE borrow_records DROP COLUMN last_reissue_date")
        conn.commit()
        print("✅ last_reissue_date column removed successfully!")
    except MySQLdb.Error as e:
        if "Can't DROP" in str(e):
            print("ℹ️  last_reissue_date column doesn't exist")
        else:
            raise
    
    # Verify the changes
    print("\n📊 Final borrow_records structure:")
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = 'borrow_records'
        ORDER BY ORDINAL_POSITION
    """, (database,))
    
    results = cursor.fetchall()
    for column_name, data_type, is_nullable in results:
        nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
        print(f"  {column_name}: {data_type} {nullable}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Database cleanup complete!")

except MySQLdb.Error as e:
    print(f"\n❌ Error: {e}")
    exit(1)
