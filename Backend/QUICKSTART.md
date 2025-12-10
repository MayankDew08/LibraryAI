# Quick Start Guide

## Setup

1. **Install Dependencies**
```bash
pip install fastapi uvicorn[standard] sqlalchemy mysqlclient python-jose[cryptography] passlib[bcrypt] python-multipart google-generativeai gtts python-dotenv
```

2. **Configure .env file**
```env
SQLALCHEMY_DATABASE_URL=mysql+mysqldb://root:yourpassword@localhost:3306/library_db
GEMINI_API_KEY=your_gemini_api_key_here
```

3. **Create MySQL Database**
```sql
CREATE DATABASE library_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

4. **Create Tables**
Run the SQL script in MySQL:
```bash
mysql -u root -p library_db < create_tables.sql
```

Or manually run the `create_tables.sql` file in MySQL Workbench/phpMyAdmin.

5. **Run the Server**
```bash
python run.py
```

Server will start at: http://localhost:8000

## API Endpoints

### Auth Routes (`/auth`)
- **POST** `/auth/register` - Register new user
- **POST** `/auth/login` - Login user

### Admin Routes (`/admin/books`)
- **POST** `/admin/books/` - Add book with PDF and cover (triggers AI generation)
- **PUT** `/admin/books/{book_id}` - Update book metadata
- **DELETE** `/admin/books/{book_id}` - Delete book

### Student Routes (`/student/books`)
- **GET** `/student/books/{book_id}/static-content` - Get AI-generated content

### Borrow Routes (`/borrow`)
- **POST** `/borrow/` - Borrow a book
- **GET** `/borrow/{borrow_id}` - Get borrow record
- **GET** `/borrow/user/{user_id}` - Get all borrows for a user
- **PUT** `/borrow/{borrow_id}/return` - Return a book
- **PUT** `/borrow/{borrow_id}/reissue` - Extend due date
- **DELETE** `/borrow/{borrow_id}` - Delete borrow record

## Testing with Swagger

1. Go to: http://localhost:8000/docs
2. Test endpoints interactively

## Testing Flow

### 1. Register a User
```json
POST /auth/register
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "password123",
  "role": "student"
}
```

### 2. Login
```json
POST /auth/login
{
  "email": "john@example.com",
  "password": "password123"
}
```

### 3. Add a Book (Admin)
```
POST /admin/books/
Form Data:
- title: "Sample Book"
- author: "John Author"
- total_copies: 5
- pdf_file: [upload PDF]
- cover_image: [upload image]
```

### 4. Get Book Content (Student)
```
GET /student/books/{book_id}/static-content
```

### 5. Borrow a Book
```json
POST /borrow/
{
  "book_id": 1,
  "user_id": 1,
  "notes": "Optional note"
}
```

### 6. Return a Book
```
PUT /borrow/{borrow_id}/return
```

## Notes

- All dates are auto-calculated
- Due date: 14 days from borrow date
- Reissue max: 3 times
- AI content generated automatically on book upload
