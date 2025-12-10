"""
Script to update status enum values in borrow_records table from lowercase to uppercase
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
    
    # First, check current enum values
    print("\n📊 Current status enum values:")
    cursor.execute("""
        SELECT COLUMN_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = 'borrow_records' 
        AND COLUMN_NAME = 'status'
    """, (database,))
    
    result = cursor.fetchone()
    if result:
        print(f"  Current: {result[0]}")
    
    # Update all existing records to uppercase
    print("\n📝 Updating existing records to uppercase...")
    cursor.execute("UPDATE borrow_records SET status = 'ACTIVE' WHERE status = 'active'")
    active_count = cursor.rowcount
    cursor.execute("UPDATE borrow_records SET status = 'RETURNED' WHERE status = 'returned'")
    returned_count = cursor.rowcount
    cursor.execute("UPDATE borrow_records SET status = 'OVERDUE' WHERE status = 'overdue'")
    overdue_count = cursor.rowcount
    conn.commit()
    print(f"  Updated {active_count} ACTIVE, {returned_count} RETURNED, {overdue_count} OVERDUE records")
    
    # Modify the enum column definition
    print("\n🔧 Modifying status column enum values to uppercase...")
    cursor.execute("""
        ALTER TABLE borrow_records 
        MODIFY COLUMN status ENUM('ACTIVE', 'RETURNED', 'OVERDUE') 
        NOT NULL DEFAULT 'ACTIVE'
    """)
    conn.commit()
    print("✅ Status column enum updated successfully!")
    
    # Verify the changes
    print("\n📊 Verifying updated enum values:")
    cursor.execute("""
        SELECT COLUMN_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = 'borrow_records' 
        AND COLUMN_NAME = 'status'
    """, (database,))
    
    result = cursor.fetchone()
    if result:
        print(f"  New: {result[0]}")
    
    # Check record counts
    cursor.execute("SELECT status, COUNT(*) FROM borrow_records GROUP BY status")
    results = cursor.fetchall()
    print("\n📊 Record counts by status:")
    for status, count in results:
        print(f"  {status}: {count}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Enum values successfully updated to uppercase!")
    print("   Status enum now: 'ACTIVE', 'RETURNED', 'OVERDUE'")

except MySQLdb.Error as e:
    print(f"\n❌ Error: {e}")
    exit(1)
