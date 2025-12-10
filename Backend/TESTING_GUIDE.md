# Testing Guide - Automatic Content Generation

## Prerequisites

1. **Install Dependencies**
```powershell
cd "d:\3Sem Minor\Backend"
pip install -r requirements.txt
```

2. **Configure Environment**
Create `Backend/.env` with:
```bash
SQLALCHEMY_DATABASE_URL=mysql+mysqldb://root:bhoolgaya@localhost:3306/library_db
GEMINI_API_KEY=REDACTED_GOOGLE_API_KEY
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

3. **Create Database Tables**
```python
from app.config.database import engine, Base
from app.models import books, static_content

Base.metadata.create_all(bind=engine)
```

## Start Server

```powershell
cd "d:\3Sem Minor\Backend"
uvicorn app.main:app --reload
```

Server will start at: `http://localhost:8000`
API docs at: `http://localhost:8000/docs`

---

## Test Workflow

### Test 1: Admin Uploads PDF (Auto-Generation)

**Using cURL:**
```bash
curl -X POST "http://localhost:8000/admin/books/" \
  -F "title=Test Book" \
  -F "author=Test Author" \
  -F "total_copies=5" \
  -F "pdf_file=@path/to/your/test.pdf" \
  -F "cover_image=@path/to/your/cover.jpg"
```

**Using Python:**
```python
import requests

url = "http://localhost:8000/admin/books/"

# Use a PDF from your Codes folder
files = {
    'pdf_file': open('d:/3Sem Minor/Codes/PS-5.pdf', 'rb'),
    'cover_image': open('path/to/cover.jpg', 'rb')
}
data = {
    'title': 'Problem Set 5',
    'author': 'Test',
    'total_copies': 5
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

**Expected Output:**
```json
{
  "message": "Book added successfully with AI-generated content",
  "book_id": 1,
  "title": "Problem Set 5",
  "author": "Test",
  "pdf_url": "/storage/pdfs/book_1_xxxxx.pdf",
  "cover_image": "/storage/covers/book_1_xxxxx.jpg",
  "content_generated": true
}
```

**What Happens Behind the Scenes:**
1. ✅ PDF uploaded to Gemini Files API
2. ✅ Gemini AI generates summary (~15 seconds)
3. ✅ Gemini AI generates Q&A pairs (~10 seconds)
4. ✅ Gemini AI generates podcast script (~10 seconds)
5. ✅ pyttsx3 generates audio file (~5 seconds)
6. ✅ All content saved to database
7. ✅ Gemini uploaded file cleaned up

**Total Processing Time:** ~40-50 seconds

---

### Test 2: Student Access Generated Content

**Using cURL:**
```bash
curl -X GET "http://localhost:8000/student/books/1/static-content"
```

**Using Python:**
```python
import requests
import json

book_id = 1
url = f"http://localhost:8000/student/books/{book_id}/static-content"

response = requests.get(url)
content = response.json()

print("=== SUMMARY ===")
print(content['summary_text'][:500] + "...")

print("\n=== Q&A PAIRS ===")
qa_pairs = json.loads(content['qa_json'])
for i, qa in enumerate(qa_pairs[:3], 1):
    print(f"\nQ{i}: {qa['question']}")
    print(f"A{i}: {qa['answer'][:200]}...")

print("\n=== PODCAST SCRIPT ===")
print(content['podcast_script'][:500] + "...")

print("\n=== FILES ===")
print(f"PDF: {content['pdf_url']}")
print(f"Audio: {content['audio_url']}")
```

**Expected Response:**
```json
{
  "content_id": 1,
  "book_id": 1,
  "pdf_url": "/storage/pdfs/book_1_xxxxx.pdf",
  "summary_text": "This comprehensive summary covers...",
  "qa_json": "[{\"question\":\"...\",\"answer\":\"...\"}]",
  "podcast_script": "Welcome to today's discussion...",
  "audio_url": "/storage/audio/podcast_book_1_xxxxx.wav",
  "created_at": "2025-12-08T10:30:00Z",
  "updated_at": "2025-12-08T10:30:00Z"
}
```

---

## Verification Checklist

### ✅ Check 1: Database Records
```sql
-- Verify book was created
SELECT * FROM books WHERE book_id = 1;

-- Verify static content was created
SELECT content_id, book_id, 
       LENGTH(summary_text) as summary_length,
       LENGTH(qa_json) as qa_length,
       LENGTH(podcast_script) as podcast_length,
       audio_url
FROM book_static_content 
WHERE book_id = 1;
```

### ✅ Check 2: Files Created
```powershell
# Check PDF was saved
ls "d:\3Sem Minor\Backend\storage\pdfs"

# Check cover image was saved
ls "d:\3Sem Minor\Backend\storage\covers"

# Check audio was generated
ls "d:\3Sem Minor\Backend\storage\audio"
```

### ✅ Check 3: Content Quality

**Summary Validation:**
- Should be comprehensive (> 500 words)
- Should cover main topics from PDF
- Should be self-contained and detailed

**Q&A Validation:**
```python
import json

qa_json = content['qa_json']
qa_pairs = json.loads(qa_json)

# Should have 10 Q&A pairs (default)
assert len(qa_pairs) == 10, "Should have 10 Q&A pairs"

# Each should have question and answer keys
for qa in qa_pairs:
    assert 'question' in qa, "Missing question key"
    assert 'answer' in qa, "Missing answer key"
    assert len(qa['question']) > 10, "Question too short"
    assert len(qa['answer']) > 20, "Answer too short"

print("✅ Q&A validation passed!")
```

**Podcast Script Validation:**
- Should be engaging and conversational
- Should NOT have speaker labels (no "Speaker1:", "Speaker2:")
- Should flow naturally like a discussion

**Audio Validation:**
```python
import os
import wave

audio_path = content['audio_url']

# Check file exists
assert os.path.exists(audio_path), "Audio file not found"

# Check it's a valid WAV file
with wave.open(audio_path, 'r') as wav:
    frames = wav.getnframes()
    rate = wav.getframerate()
    duration = frames / float(rate)
    print(f"✅ Audio: {duration:.1f} seconds, {rate} Hz")
```

### ✅ Check 4: API Response Time
```python
import time
import requests

start = time.time()
response = requests.post(url, files=files, data=data)
elapsed = time.time() - start

print(f"Total time: {elapsed:.1f} seconds")
# Should be 40-60 seconds for complete generation
```

---

## Troubleshooting

### Problem: "No module named 'google.genai'"
**Solution:**
```powershell
pip uninstall google-generativeai
pip install google-genai==0.3.0
```

### Problem: "pyttsx3 init failed"
**Solution (Windows):**
```powershell
# Install required dependencies
pip install pywin32
pip install pyttsx3==2.98
```

### Problem: "Content generation failed"
**Check:**
1. Gemini API key is correct in `.env`
2. PDF is valid and not corrupted
3. Check terminal logs for specific error
4. Verify internet connection (for Gemini API calls)

### Problem: "Audio file not created"
**Check:**
```python
# Test pyttsx3 directly
import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')
print(f"Available voices: {len(voices)}")
for voice in voices:
    print(f"  - {voice.name}")

# Test audio generation
engine.say("This is a test")
engine.runAndWait()
```

### Problem: "Database connection failed"
**Solution:**
```powershell
# Verify MySQL is running
Get-Service -Name MySQL*

# Test connection
mysql -u root -p
USE library_db;
SHOW TABLES;
```

---

## Performance Benchmarks

### Expected Processing Times (by PDF size):

| PDF Size | Pages | Gemini AI | Audio Gen | Total Time |
|----------|-------|-----------|-----------|------------|
| Small    | 1-10  | 15-20s    | 3-5s      | 20-25s     |
| Medium   | 11-50 | 25-35s    | 5-8s      | 30-45s     |
| Large    | 51+   | 40-60s    | 8-12s     | 50-75s     |

### Content Size (typical):
- **Summary:** 2,000-5,000 words (15-40 KB)
- **Q&A JSON:** 10 pairs (~5-10 KB)
- **Podcast Script:** 3,000-6,000 words (20-50 KB)
- **Audio WAV:** 2-5 MB per minute

---

## Success Indicators

✅ **Upload Response:** `content_generated: true`
✅ **Database:** Record in `book_static_content` table
✅ **Files:** PDF, cover, and WAV audio files created
✅ **Content:** All fields populated (summary, qa_json, podcast_script, audio_url)
✅ **Student Access:** GET endpoint returns complete content
✅ **Audio Quality:** Clear, professional-sounding podcast at 185 WPM
✅ **Q&A Format:** Valid JSON with 10 question-answer pairs
✅ **No Errors:** Server logs show successful generation

---

## Next Steps After Verification

1. **Test with Multiple PDFs** - Verify different PDF sizes/types
2. **Load Testing** - Test concurrent uploads
3. **Frontend Integration** - Connect React/Vue frontend
4. **Error Handling** - Test edge cases (corrupted PDFs, huge files)
5. **Monitoring** - Add logging for generation times
6. **Caching** - Consider caching frequently accessed content
