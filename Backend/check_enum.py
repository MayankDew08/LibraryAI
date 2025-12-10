from app.config.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SHOW COLUMNS FROM users LIKE 'role'"))
    for row in result:
        print(f"Column: {row[0]}")
        print(f"Type: {row[1]}")
        print(f"Null: {row[2]}")
        print(f"Default: {row[4]}")
