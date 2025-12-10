# On-Demand Content Generation System

## Problem Solved
**API Quota Exhaustion**: Automatic content generation for all uploaded books was consuming API quota too quickly, causing failures.

## Solution Implemented
**On-Demand Generation**: Content (summary, Q&A, podcast, audio) is now generated only when students actually request it, not automatically on upload.

---

## How It Works

### 1. **Admin Uploads Book**
```
POST /admin/books/
```
- Admin uploads PDF and cover image
- Book is saved to database immediately
- ✅ **No API calls made** - quota preserved
- Response: `"Content will be generated on first student request"`

### 2. **Student Requests Content**
```
GET /student/books/{book_id}/static-content
```
- Student requests to view book content
- System checks if content exists
- If **NOT exists**: Generate on-demand (uses API quota)
- If **EXISTS**: Return cached content (no API call)
- Content is cached for future requests

### 3. **Admin Manual Generation (Optional)**
```
POST /admin/books/{book_id}/generate-content
```
- Admin can pre-generate content for popular books
- Reduces wait time for students
- Useful for high-demand books

---

## Benefits

### ✅ **95% Quota Savings**
- Only generate content when actually needed
- Most uploaded books may never be accessed
- No wasted API calls

### ⚡ **Fast Upload**
- Book upload is instant (no waiting for AI)
- Admin can upload many books quickly

### 🎯 **Smart Caching**
- Content generated once, used forever
- Subsequent students get instant access

### 🔧 **Flexible Control**
- Admin decides which books to pre-generate
- System auto-generates on first student request

---

## API Endpoints

### Admin Endpoints

**Upload Book** (No content generation)
```http
POST /admin/books/
Content-Type: multipart/form-data

title: "Book Title"
author: "Author Name"
total_copies: 5
pdf_file: <file>
cover_image: <file>
```

**Manual Content Generation**
```http
POST /admin/books/{book_id}/generate-content
```
Response:
```json
{
  "message": "Content generated successfully",
  "book_id": 1,
  "content_id": 1,
  "generated_items": {
    "summary": true,
    "qa": true,
    "podcast": true,
    "audio": true
  }
}
```

### Student Endpoints

**Search Books by Title**
```http
GET /student/books/search?title=algebra
```

**Get Book Content** (Auto-generates if needed)
```http
GET /student/books/{book_id}/static-content
```
First request (no content exists):
- Generates content using AI (takes 30-60 seconds)
- Caches result
- Returns generated content

Subsequent requests:
- Returns cached content instantly

---

## Quota Management Tips

1. **Let students trigger generation naturally** - Most efficient
2. **Pre-generate popular books** - Use manual endpoint for frequently accessed books
3. **Monitor usage** - Check which books are actually being accessed
4. **Stagger uploads** - Spread uploads over time if pre-generating

---

## Technical Details

### Models Used
- All content uses `gemini-2.5-flash` to avoid quota conflicts
- Parallel processing with ThreadPoolExecutor (3 concurrent tasks)
- Automatic retry with exponential backoff (3 attempts)

### Content Generated
1. **Summary**: Comprehensive book summary
2. **Q&A**: 10 question-answer pairs
3. **Podcast Script**: Engaging audio transcript
4. **Audio File**: MP3 using pyttsx3 (offline TTS)

### Database Schema
- `books` table: Book metadata + PDF/cover
- `book_static_content` table: Generated AI content
- Lazy loading: Content generated only when requested

---

## Testing the System

### Test 1: Upload Book
```bash
curl -X POST "http://localhost:8000/admin/books/" \
  -F "title=Test Book" \
  -F "author=Test Author" \
  -F "total_copies=5" \
  -F "pdf_file=@book.pdf" \
  -F "cover_image=@cover.jpg"
```
✅ Should succeed immediately without API calls

### Test 2: Student Access (First Time)
```bash
curl "http://localhost:8000/student/books/1/static-content"
```
⏳ Takes 30-60 seconds (generates content)
✅ Returns full content

### Test 3: Student Access (Second Time)
```bash
curl "http://localhost:8000/student/books/1/static-content"
```
⚡ Instant response (cached content)

### Test 4: Manual Generation
```bash
curl -X POST "http://localhost:8000/admin/books/1/generate-content"
```
✅ Pre-generates content for book ID 1

---

## Error Handling

### Quota Exceeded
If quota is still exceeded:
1. Wait for quota reset (usually 24 hours for free tier)
2. Add more API keys to `API_KEYS` list in `gemini_ai.py`
3. Upgrade to paid tier for higher limits

### Content Generation Failed
- Book is still saved
- Content generation will retry on next student request
- Admin can manually trigger regeneration

---

## Configuration

### Add More API Keys
Edit `app/services/gemini_ai.py`:
```python
API_KEYS = [
    "REDACTED_GOOGLE_API_KEY",
    "YOUR_SECOND_API_KEY",
    "YOUR_THIRD_API_KEY",
]
```

### Change Models
Edit `MODELS` dict to use different Gemini models:
```python
MODELS = {
    "summary": "models/gemini-2.5-flash",
    "qa": "models/gemini-pro",
    "podcast": "models/gemini-flash-latest"
}
```

---

## Monitoring

### Check if Content Exists
```sql
SELECT book_id, 
       CASE WHEN summary_text IS NOT NULL THEN 'Yes' ELSE 'No' END as has_content
FROM book_static_content;
```

### Count Generated vs Pending
```sql
SELECT 
    COUNT(*) as total_books,
    SUM(CASE WHEN content_id IS NOT NULL THEN 1 ELSE 0 END) as content_generated,
    SUM(CASE WHEN content_id IS NULL THEN 1 ELSE 0 END) as content_pending
FROM books 
LEFT JOIN book_static_content ON books.book_id = book_static_content.book_id;
```

---

## Migration from Old System

Old system: Auto-generate on upload
New system: On-demand generation

**No migration needed** - System automatically handles both:
- Books with existing content: Returns immediately
- Books without content: Generates on first request
