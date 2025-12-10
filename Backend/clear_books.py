from app.config.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Disable foreign key checks temporarily
    conn.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
    
    # Clear tables in correct order
    conn.execute(text('DELETE FROM book_static_content'))
    conn.execute(text('DELETE FROM borrow_records'))
    conn.execute(text('DELETE FROM books'))
    
    # Re-enable foreign key checks
    conn.execute(text('SET FOREIGN_KEY_CHECKS = 1'))
    
    conn.commit()
    print('Books and related tables cleared successfully')
