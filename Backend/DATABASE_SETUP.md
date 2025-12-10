# Database Setup Guide

## MySQL Configuration

### 1. Update Database Credentials

Edit `app/config/database.py` and update the connection string:

```python
SQLALCHEMY_DATABASE_URL = "mysql+mysqldb://username:password@host:port/database_name"
```

**Example:**
```python
SQLALCHEMY_DATABASE_URL = "mysql+mysqldb://root:mypassword@localhost:3306/library_db"
```

### 2. Create MySQL Database

```sql
CREATE DATABASE library_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Install Required Dependencies

```bash
pip install sqlalchemy mysqlclient
```

### 4. Initialize Database Tables

Run the initialization script:

```bash
python -m app.config.init_db
```

## Model Features

### User Model
- **Email validation**: 255 character limit, unique constraint
- **Roles**: STUDENT, FACULTY, ADMIN
- **Timestamps**: `created_at`, `updated_at`
- **Soft delete**: `is_active` flag
- **Relationships**: One-to-many with borrow records

### Books Model
- **String constraints**: Proper length limits (title: 255, isbn: 20, etc.)
- **Additional fields**: publisher, publication_year, category, description
- **Check constraints**: 
  - `available_copies >= 0`
  - `total_copies >= 0`
  - `available_copies <= total_copies`
- **Relationships**: One-to-many with borrow records

### Borrow Model
- **Foreign keys**: Properly linked to users and books with CASCADE delete
- **Automatic due date**: Calculated as 14 days from borrowed_date
- **Reissue functionality**: 
  - Maximum 3 reissues per borrow
  - Tracks `reissue_count` and `last_reissue_date`
  - Method: `reissue(extension_days=14)`
- **Status tracking**: ACTIVE, RETURNED, OVERDUE
- **Helper methods**:
  - `mark_returned()`: Mark book as returned
  - `check_overdue()`: Check and update overdue status

## Usage Examples

### Creating a Borrow Record (Auto Due Date)

```python
from app.models.borrow import Borrow
from datetime import datetime

# Due date is automatically calculated (14 days from now)
borrow = Borrow(
    user_id=1,
    book_id=5
)
# borrow.due_date will be automatically set to 14 days from borrowed_date
```

### Reissuing a Book

```python
# Get borrow record
borrow = session.query(Borrow).filter(Borrow.borrow_id == 1).first()

# Extend due date by 14 more days
borrow.reissue(extension_days=14)
session.commit()
```

### Returning a Book

```python
borrow.mark_returned()
session.commit()
```

### Checking Overdue Status

```python
is_overdue = borrow.check_overdue()
session.commit()
```

## Email Validation

The User model has email field with:
- Maximum length: 255 characters
- Unique constraint
- Indexed for fast lookups
- Required field (nullable=False)

For additional email format validation, use Pydantic schemas:

```python
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr  # Validates email format
    name: str
    password: str
```

## Database Indexes

All models include appropriate indexes for:
- Primary keys (auto-indexed)
- Foreign keys
- Frequently queried fields (email, isbn, dates, status)

## Migration Notes

When changing from SQLite to MySQL:
- Boolean fields changed to Integer (0/1) for MySQL compatibility
- String fields now have explicit lengths
- DateTime fields use `datetime.utcnow` instead of `datetime.datetime.utcnow`
- Proper foreign key constraints with CASCADE delete
- Check constraints for data validation
