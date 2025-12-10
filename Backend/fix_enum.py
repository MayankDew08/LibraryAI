from app.config.database import engine
from sqlalchemy import text

# Update the users table role enum to use lowercase values
with engine.connect() as conn:
    # First, alter the enum to include both uppercase and lowercase
    conn.execute(text("""
        ALTER TABLE users 
        MODIFY COLUMN role ENUM('student', 'faculty', 'admin', 'STUDENT', 'FACULTY', 'ADMIN') 
        NOT NULL DEFAULT 'student'
    """))
    
    # Update any existing uppercase values to lowercase
    conn.execute(text("UPDATE users SET role = LOWER(role)"))
    
    # Now remove the uppercase values from enum
    conn.execute(text("""
        ALTER TABLE users 
        MODIFY COLUMN role ENUM('student', 'faculty', 'admin') 
        NOT NULL DEFAULT 'student'
    """))
    
    conn.commit()
    print('Database enum updated to use lowercase values')
