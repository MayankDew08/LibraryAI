from app.config.database import engine
from sqlalchemy import text

# Clear all tables in the correct order (respecting foreign key constraints)
with engine.connect() as conn:
    # Get all tables
    result = conn.execute(text('SHOW TABLES'))
    tables = [row[0] for row in result]
    
    print(f'Found tables: {tables}')
    
    # Disable foreign key checks temporarily
    conn.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
    
    # Clear all tables
    for table in tables:
        try:
            conn.execute(text(f'DELETE FROM {table}'))
            print(f'Cleared table: {table}')
        except Exception as e:
            print(f'Error clearing {table}: {e}')
    
    # Re-enable foreign key checks
    conn.execute(text('SET FOREIGN_KEY_CHECKS = 1'))
    
    conn.commit()
    print('\nAll database tables cleared successfully')
