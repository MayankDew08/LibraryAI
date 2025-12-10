# API Endpoints - Automatic Content Generation Flow

## 📚 Admin Workflow: Upload PDF → Auto-Generate All Content

### 1. Admin Uploads PDF Book
**Endpoint:** `POST /admin/books/`

**What happens automatically:**
1. ✅ PDF and cover image saved to storage
2. ✅ Book record created in database
3. ✅ **Gemini AI generates:**
   - Comprehensive summary
   - Q&A pairs (JSON format)
   - Podcast-style transcript
4. ✅ **Audio generated** using pyttsx3 (fast offline TTS)
5. ✅ All content saved to `book_static_content` table
6. ✅ Students can immediately access content

**Request:**
```bash
POST http://localhost:8000/admin/books/
Content-Type: multipart/form-data

Form Data:
- title: "Linear Algebra Done Right"
- author: "Sheldon Axler"
- total_copies: 10
- pdf_file: [PDF file]
- cover_image: [Image file]
```

**Response:**
```json
{
  "message": "Book added successfully with AI-generated content",
  "book_id": 123,
  "title": "Linear Algebra Done Right",
  "author": "Sheldon Axler",
  "pdf_url": "/storage/pdfs/book_123_1234567890.pdf",
  "cover_image": "/storage/covers/book_123_1234567890.jpg",
  "content_generated": true
}
```

---

## 👨‍🎓 Student Workflow: Access Generated Content

### 2. Student Gets All Generated Content
**Endpoint:** `GET /student/books/{book_id}/static-content`

**What students receive:**
- ✅ Summary text (comprehensive, detailed)
- ✅ Q&A pairs (JSON array with questions and answers)
- ✅ Podcast script (engaging, conversational)
- ✅ Audio file URL (WAV format, ready to play)
- ✅ PDF URL (original document)

**Request:**
```bash
GET http://localhost:8000/student/books/123/static-content
```

**Response:**
```json
{
  "content_id": 456,
  "book_id": 123,
  "pdf_url": "/storage/pdfs/book_123_1234567890.pdf",
  "summary_text": "This comprehensive summary covers the key concepts of linear algebra...",
  "qa_json": "[{\"question\":\"What is a vector space?\",\"answer\":\"A vector space is a set of objects called vectors...\"}]",
  "podcast_script": "Welcome to today's discussion on Linear Algebra! Let's dive into the fascinating world of vector spaces...",
  "audio_url": "/storage/audio/podcast_book_123_1234567890.wav",
  "created_at": "2025-12-08T10:30:00Z",
  "updated_at": "2025-12-08T10:30:00Z"
}
```

---

## 🔄 Complete Data Flow

```
Admin Uploads PDF
       ↓
[admin_books.py] POST /admin/books/
       ↓
[admin_books.py] add_book_with_files()
       ↓
1. Save PDF & cover image
2. Create book record
       ↓
[static_content_service.py] create_static_content()
       ↓
[gemini_ai.py] generate_all_content(pdf_path)
   ├─ upload_pdf_to_gemini() ──→ Upload to Gemini Files API
   ├─ generate_summary() ──────→ AI generates comprehensive summary
   ├─ generate_qa_pairs() ─────→ AI generates Q&A JSON
   ├─ generate_podcast_script()→ AI generates engaging transcript
   └─ cleanup_uploaded_file() ─→ Delete from Gemini (cleanup)
       ↓
[audio_generation.py] generate_podcast_audio()
   ├─ extract_clean_content() ─→ Remove markdown formatting
   ├─ setup_tts_engine() ──────→ Configure pyttsx3 (185 WPM)
   └─ Save WAV file ───────────→ Fast offline generation (5-10s)
       ↓
Save to database: book_static_content table
       ↓
✅ Content ready for students!
       ↓
Student Requests
[student_books.py] GET /student/books/{book_id}/static-content
       ↓
[student_books.py] get_static_content()
       ↓
Return all generated content (summary, Q&A, podcast, audio, PDF)
```

---

## 🗄️ Database Schema

### `books` table
```sql
book_id (PK)
title
author
pdf_url          -- Stored PDF path
cover_image      -- Stored cover image path
total_copies
available_copies
created_at
updated_at
```

### `book_static_content` table
```sql
content_id (PK)
book_id (FK) → books.book_id (UNIQUE - one content per book)
summary_text     -- AI-generated comprehensive summary
qa_json          -- AI-generated Q&A pairs as JSON string
podcast_script   -- AI-generated podcast transcript
audio_url        -- Generated audio file path (WAV)
created_at       -- When content was generated
updated_at       -- Last regeneration time
```

**Relationship:** One book has one static_content (1:1)

---

## ⚡ Performance & Features

### Generation Speed
- **Gemini AI Processing:** ~10-30 seconds (depends on PDF size)
- **Audio Generation (pyttsx3):** ~5-10 seconds (offline, fast)
- **Total Time:** ~15-40 seconds for complete content generation

### Content Quality
- **Summary:** Comprehensive, detailed, self-contained
- **Q&A:** 10 question-answer pairs in valid JSON format
- **Podcast:** Engaging, conversational, no speaker labels
- **Audio:** Professional quality, 185 WPM, clear voice

### Automatic Features
✅ **Auto-cleanup:** Uploaded files removed from Gemini after processing
✅ **Error handling:** If content generation fails, book is still saved
✅ **Cascade delete:** Deleting a book removes all associated content
✅ **Unique constraint:** One content record per book

---

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Gemini AI - Working API key from Codes folder
GEMINI_API_KEY=REDACTED_GOOGLE_API_KEY

# Database
SQLALCHEMY_DATABASE_URL=mysql+mysqldb://root:password@localhost:3306/library_db

# Storage paths (configured in settings.py)
PDF_STORAGE_DIR=./storage/pdfs
COVER_STORAGE_DIR=./storage/covers
AUDIO_OUTPUT_DIR=./storage/audio
```

### AI Model Settings
- **Model:** gemini-2.5-flash
- **SDK:** google-genai (Client-based)
- **Temperature:** 0.7 (balanced creativity/consistency)

### TTS Settings
- **Engine:** pyttsx3 (offline, fast)
- **Rate:** 185 WPM (professional pace)
- **Volume:** 0.9
- **Format:** WAV audio
- **Voice:** Auto-selected (prefers male voices for professional sound)

---

## 📝 Example Usage

### Admin Uploads Book
```python
import requests

url = "http://localhost:8000/admin/books/"
files = {
    'pdf_file': open('linear_algebra.pdf', 'rb'),
    'cover_image': open('cover.jpg', 'rb')
}
data = {
    'title': 'Linear Algebra Done Right',
    'author': 'Sheldon Axler',
    'total_copies': 10
}

response = requests.post(url, files=files, data=data)
print(response.json())
# {
#   "message": "Book added successfully with AI-generated content",
#   "book_id": 123,
#   "content_generated": true
# }
```

### Student Gets Content
```python
import requests
import json

book_id = 123
url = f"http://localhost:8000/student/books/{book_id}/static-content"

response = requests.get(url)
content = response.json()

# Access summary
print(content['summary_text'])

# Parse Q&A JSON
qa_pairs = json.loads(content['qa_json'])
for qa in qa_pairs:
    print(f"Q: {qa['question']}")
    print(f"A: {qa['answer']}\n")

# Get audio file
audio_url = content['audio_url']
print(f"Listen at: {audio_url}")

# Get PDF
pdf_url = content['pdf_url']
print(f"Download PDF: {pdf_url}")
```

---

## 🎯 Key Benefits

### For Admins
- ✅ **One-step upload** - Just upload PDF, everything else is automatic
- ✅ **No manual work** - AI generates all content automatically
- ✅ **Fast processing** - Complete in 15-40 seconds
- ✅ **Error recovery** - Book saved even if content generation fails

### For Students
- ✅ **Instant access** - Content available immediately after upload
- ✅ **Multiple formats** - Summary, Q&A, podcast script, audio, PDF
- ✅ **High quality** - Professional AI-generated content
- ✅ **Audio support** - Listen to podcast version of the book
- ✅ **Study aids** - Q&A pairs for quick review

### Technical
- ✅ **Offline TTS** - No internet required for audio generation
- ✅ **Fast performance** - pyttsx3 is 3-6x faster than gTTS
- ✅ **Resource cleanup** - Automatic file cleanup from Gemini
- ✅ **Database integrity** - Foreign key constraints and cascading deletes
- ✅ **One-to-one mapping** - Each book has exactly one content record
