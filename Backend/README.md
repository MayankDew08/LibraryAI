# Library Management System - Backend Setup

## Overview
This backend system uses Gemini AI to automatically generate educational content from book PDFs.

## Features
- **Automated Content Generation**: Upload PDF and cover image → AI generates:
  - Comprehensive book summary
  - Q&A pairs for studying
  - Podcast script
  - Text-to-speech podcast audio
- **MySQL Database**: Professional database with proper constraints and relationships
- **File Management**: Automatic storage of PDFs, cover images, and audio files
- **User Authentication**: Password hashing with role-based access (Student, Faculty, Admin)

## Installation

### 1. Install Dependencies

```bash
pip install fastapi uvicorn[standard] sqlalchemy mysqlclient python-jose[cryptography] passlib[bcrypt] python-multipart google-generativeai gtts python-dotenv
```

### 2. Configure Environment Variables

Create/update `.env` file:

```env
SQLALCHEMY_DATABASE_URL=mysql+mysqldb://root:yourpassword@localhost:3306/library_db
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_secret_key_here
```

**Get Gemini API Key**: https://aistudio.google.com/app/apikey

### 3. Create MySQL Database

```sql
CREATE DATABASE library_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Initialize Database Tables

```bash
python -m app.config.init_db
```

## How It Works

### Admin Flow: Adding a Book

1. **Admin uploads**:
   - Book PDF file
   - Cover image (JPG/PNG/WEBP)
   - Basic metadata (title, author, copies)

2. **System automatically**:
   - Saves files to `static/` folders
   - Uploads PDF to Gemini AI
   - Generates comprehensive summary
   - Creates Q&A pairs (10 questions)
   - Writes engaging podcast script
   - Converts script to audio (MP3)
   - Saves everything to database

3. **Students get**:
   - Full book PDF
   - AI-generated summary
   - Study Q&A
   - Podcast to listen to

### Service Architecture

```
admin_books.py
  ↓ (uploads PDF & cover)
  ↓
static_content_service.py
  ↓ (orchestrates generation)
  ↓
gemini_ai.py → Generates summary, Q&A, script
  ↓
audio_generation.py → Converts script to MP3
  ↓
Database (all content saved)
```

## File Structure

```
static/
  ├── pdfs/          # Book PDF files
  ├── covers/        # Cover images
  └── podcasts/      # Generated audio files
```

## API Services

### `admin_books.py`
- `add_book_with_files()`: Upload book with PDF and cover, triggers AI generation

### `gemini_ai.py`
- `generate_all_content()`: Orchestrates all AI generation
- `generate_summary()`: Creates book summary
- `generate_qa_pairs()`: Creates Q&A JSON
- `generate_podcast_script()`: Creates podcast script

### `audio_generation.py`
- `generate_podcast_audio()`: Converts script to MP3 using gTTS

### `static_content_service.py`
- `create_static_content()`: Saves all generated content to database
- `regenerate_static_content()`: Regenerates content for existing books

## Database Models

All models use:
- Proper foreign keys with CASCADE delete
- Timezone-aware timestamps
- String length constraints for MySQL
- Automatic date calculations

### StaticContent Model
```python
- content_id (PK)
- book_id (FK → books.book_id, unique)
- summary_text (Text)
- qa_json (Text - JSON string)
- podcast_script (Text)
- audio_url (String)
- created_at, updated_at
```

## Requirements

**Minimum:**
- Python 3.10+
- MySQL 5.7+
- Gemini API key (free tier available)

**Python Packages:**
```
fastapi
uvicorn[standard]
sqlalchemy
mysqlclient
python-jose[cryptography]
passlib[bcrypt]
python-multipart
google-generativeai
gtts
python-dotenv
```

## Notes

- **PDF Processing**: Gemini AI handles PDF parsing automatically
- **Audio Generation**: Uses Google Text-to-Speech (free, no API key needed)
- **File Storage**: All files stored locally in `static/` directory
- **Error Handling**: If AI generation fails, book is still saved but marked with error
- **Regeneration**: Content can be regenerated anytime for existing books

## Security

- Passwords hashed with bcrypt
- Email validation with Pydantic EmailStr
- Role-based access control (Student/Faculty/Admin)
- File type validation for uploads
- SQL injection protection via SQLAlchemy ORM
