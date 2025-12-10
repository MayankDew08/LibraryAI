"""
Script to alter book_static_content columns from TEXT to LONGTEXT
Run this to fix the "Data too long for column" error
"""
import MySQLdb
from app.config.database import SQLALCHEMY_DATABASE_URL
import re

# Parse database URL
# Format: mysql+mysqldb://user:password@host:port/database
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
    
    # Alter columns to LONGTEXT
    alterations = [
        "ALTER TABLE book_static_content MODIFY COLUMN summary_text LONGTEXT",
        "ALTER TABLE book_static_content MODIFY COLUMN qa_json LONGTEXT",
        "ALTER TABLE book_static_content MODIFY COLUMN podcast_script LONGTEXT"
    ]
    
    for sql in alterations:
        print(f"\nExecuting: {sql}")
        cursor.execute(sql)
        conn.commit()
        print("✅ Success!")
    
    # Verify the changes
    print("\n📊 Verifying column types:")
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = 'book_static_content' 
        AND COLUMN_NAME IN ('summary_text', 'qa_json', 'podcast_script')
    """, (database,))
    
    results = cursor.fetchall()
    for column_name, data_type, max_length in results:
        max_len_display = max_length if max_length else "4,294,967,295 (4GB)"
        print(f"  {column_name}: {data_type} (max: {max_len_display} chars)")
    
    cursor.close()
    conn.close()
    
    print("\n✅ All columns successfully altered to LONGTEXT!")
    print("   - summary_text: LONGTEXT (up to 4GB)")
    print("   - qa_json: LONGTEXT (up to 4GB)")
    print("   - podcast_script: LONGTEXT (up to 4GB)")
    print("\n🎉 You can now store large content without truncation!")

except MySQLdb.Error as e:
    print(f"\n❌ Error: {e}")
    exit(1)
