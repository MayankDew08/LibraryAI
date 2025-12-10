from app.config.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text('DELETE FROM users'))
    conn.commit()
    print('Users table cleared successfully')
