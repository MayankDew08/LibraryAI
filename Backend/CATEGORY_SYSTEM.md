# Category System Documentation

## Overview
The library system now supports **multiple categories per book** using a many-to-many relationship.

## Database Schema Changes

### New Tables
1. **`categories`** - Stores unique category names
   - `category_id` (PK)
   - `name` (unique, indexed)

2. **`book_categories`** - Junction table (many-to-many)
   - `book_id` (FK to books)
   - `category_id` (FK to categories)

### Modified Tables
- **`books`** - Removed single `category` column
- **`books`** - `title` and `author` now NOT NULL

---

## Migration Instructions

### 1. Run Migration Script
```bash
conda activate audiolib
cd Backend
python migrate_to_categories.py
```

The script will:
- ✅ Create new tables (`categories`, `book_categories`)
- ✅ Migrate existing category data
- ✅ Drop old `category` column
- ✅ Update title/author constraints

### 2. Restart Server
```bash
# Stop current server (Ctrl+C)
uvicorn app.main:app --reload
```

---

## API Usage

### Admin: Add Book with Categories

**Endpoint:** `POST /admin/books/`

**Form Data:**
```
title: "Atomic Habits"
author: "James Clear"
total_copies: 5
categories: "Self-Help,Psychology,Business"  ← Comma-separated!
pdf_file: <file>
cover_image: <file>
```

**Response:**
```json
{
  "message": "Book and all content generated successfully",
  "book_id": 1,
  "title": "Atomic Habits",
  "author": "James Clear",
  "categories": ["Self-Help", "Psychology", "Business"],
  "pdf_url": "static/pdfs/...",
  "cover_image": "static/covers/...",
  "content_generated": true,
  "rag_indexed": true
}
```

### Admin: Quick Add (RAG Only)

**Endpoint:** `POST /admin/books/quick-add`

Same parameters as above, but skips summary/Q&A/podcast generation.

---

### Student: Search Books

**Endpoint:** `GET /student/books/search`

**Query Parameters (all optional):**
- `title` - Search by title (partial match)
- `author` - Search by author (partial match)
- `categories` - Comma-separated categories (exact match)

**Examples:**

1. **Search by title:**
   ```
   GET /student/books/search?title=atomic
   ```

2. **Search by author:**
   ```
   GET /student/books/search?author=clear
   ```

3. **Search by categories:**
   ```
   GET /student/books/search?categories=Self-Help,Psychology
   ```
   Returns books that have ANY of these categories.

4. **Combined search:**
   ```
   GET /student/books/search?title=habits&author=clear&categories=Self-Help
   ```

**Response:**
```json
[
  {
    "book_id": 1,
    "title": "Atomic Habits",
    "author": "James Clear",
    "categories": ["Self-Help", "Psychology", "Business"],
    "available_copies": 3,
    "total_copies": 5,
    "cover_image": "static/covers/...",
    "pdf_url": "static/pdfs/..."
  }
]
```

### Student: List All Books

**Endpoint:** `GET /student/books/`

Now includes `categories` array in response.

### Admin: List All Books

**Endpoint:** `GET /admin/books/`

Now includes `categories` array in response.

---

## Common Categories

Suggested categories for your library:
- **Self-Help**
- **Psychology**
- **Business**
- **Fiction**
- **Non-Fiction**
- **Biography**
- **Science**
- **Technology**
- **Philosophy**
- **History**
- **Finance**
- **Health**
- **Productivity**

---

## Important Notes

### ✅ What Works
- Multiple categories per book
- Search by title, author, or categories
- All existing endpoints updated
- Backward compatible API (added categories field)

### ⚠️ Important Rules
1. **Categories are required** - At least one category must be provided
2. **Comma-separated format** - Use commas to separate multiple categories
3. **No duplicates** - System automatically removes duplicate categories
4. **Case-sensitive** - "Self-Help" ≠ "self-help" (be consistent!)

### 🚫 Not Affected
These services remain unchanged:
- ✅ RAG chat system
- ✅ Content generation (summary, Q&A, podcast)
- ✅ Borrow/return system
- ✅ Static content service
- ✅ Authentication

---

## Testing Checklist

### Before Migration
- [ ] Backup database
- [ ] Note existing books and their categories

### After Migration
- [ ] Verify all books still exist
- [ ] Check categories migrated correctly
- [ ] Test adding new book with multiple categories
- [ ] Test search by title
- [ ] Test search by author
- [ ] Test search by categories
- [ ] Test combined search
- [ ] Verify existing features (borrow, RAG, etc.)

---

## Rollback (Emergency)

If migration fails, restore from backup:
```sql
-- Restore database from backup
mysql -u root -p library_db < backup.sql
```

---

## Frontend Updates (Coming Soon)

Frontend changes needed:
1. **Admin Add Book Form:**
   - Add category input field (multi-select or tags)
   - Pass categories as comma-separated string

2. **Student Search:**
   - Add category filter dropdown
   - Add author search input

3. **Book Display:**
   - Show category badges/tags

**Note:** Backend is ready, frontend updates pending.
