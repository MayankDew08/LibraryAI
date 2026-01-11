# LibraryAI — Backend (FastAPI)

See the project overview in the repository root: `README.md`.

A production-minded backend for LibraryAI with **traditional LMS workflows** (inventory, borrowing, fines, users/admins) and **AI augmentation** (on-demand summaries/Q&A/podcasts + full RAG chat over uploaded PDFs).

This backend is intentionally “deep” for a student project: it blends **CRUD + auth + DB constraints** with **PDF ingestion pipelines**, **vector search**, **async caching**, **profiling**, and **load testing**.

## What’s inside (high level)

- **FastAPI** app with modular routes/services/models
- **MySQL + SQLAlchemy** for core data (books, users, borrow records, categories, static content)
- **OTP-first authentication flows** for student + admin onboarding/login
- **JWT-based security** (bearer access tokens + role-aware route protection)
- **Borrowing system** with due dates, overdue detection, and fine calculation
- **AI content generation** (summary / Q&A / podcast script + offline TTS audio)
- **RAG chat**: PDF → cleaned text → chunking → embeddings → ChromaDB → MMR retrieval → Gemini answer generation
- **Redis caching** for expensive AI/RAG calls
- **Targeted profiling** (cProfile) for RAG query requests only
- **Locust load testing** to push the API under concurrent traffic

## Backend “infra complexity” highlights

This isn’t just endpoints—there are multiple subsystems working together:

1. **Document ingestion + vector persistence**
   - Each book gets a dedicated Chroma collection: `book_{book_id}`
   - Embeddings are stored on disk under `static/vectordb/` (persistent local vector DB)

2. **RAG retrieval quality**
   - Uses **MMR (Maximal Marginal Relevance)** to balance relevance + diversity
   - Prevents “5 chunks that all say the same thing” and improves answer coverage

3. **Performance engineering**
   - RAG endpoints are the most expensive path; this backend includes:
     - **Redis cache** keyed by `(book_id, question, num_chunks)`
     - **cProfile middleware** that profiles only `POST /rag/books/{id}/query`

4. **On-demand content generation**
   - Students can trigger generation for **public** books; the first generation is stored and reused
   - System-level caching/invalidation prevents repeat costs

5. **Operational realism**
   - Email delivery via SendGrid for OTP + notifications
   - Static file serving for PDFs/covers/audio
   - A load test client (Locust) to validate system behavior under pressure

6. **Security boundaries + data integrity**
  - JWT bearer auth with token expiry (configurable)
  - Admin-only routes enforced with dependencies (example: admin book management + borrow verifications)
  - DB-level constraints for inventory correctness (e.g., `available_copies <= total_copies`)
  - Public vs confidential book gating for student-triggered AI generation

## Security model (JWT + OTP)

- **OTP gates authentication**: students/admins generate an OTP and verify it during register/login.
- **Passwords are hashed** (bcrypt) before storage.
- **JWT access tokens** are issued on successful registration/login and used as `Authorization: Bearer <token>`.
- **Role-aware protection**:
  - Admin endpoints depend on an authenticated admin token (e.g. `/admin/books/*`, admin borrow verification endpoints).
  - Student flows enforce student role and additional policy checks (e.g. student generation allowed only when `is_public == 1`).

Practical note: OTP endpoints currently return the OTP in the response for development convenience; remove that field for production.

## Project layout

```text
Backend/
  app/
    main.py                 # FastAPI app + middleware + router mounting
    config/                 # settings + DB connection
    models/                 # SQLAlchemy models
    routes/                 # API routes
    schemas/                # Pydantic schemas
    services/               # business logic (AI, RAG, auth, borrowing, etc.)
    utils/                  # storage + security helpers

  static/
    pdfs/                   # uploaded PDFs
    covers/                 # cover images
    podcasts/               # generated audio files
    vectordb/               # persistent ChromaDB collections

  locust/
    locustfile.py           # load test tasks

  docs/
    SETUP.md
    ARCHITECTURE.md
    LOAD_TESTING.md

  run.py                    # local dev entrypoint
  requirements.txt
  .env.example
```

## Quickstart (Windows / PowerShell)

1) Create a virtual environment (or use conda) and install dependencies:

```powershell
cd "D:\3Sem Minor\Backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Create your environment file:

```powershell
Copy-Item .env.example .env
```

3) Start dependencies:

- **MySQL** must be running and `SQLALCHEMY_DATABASE_URL` must point to a valid database.
- **Redis** must be running on `localhost:6379` (used by both RAG and on-demand generation caching).

4) Run the API:

```powershell
python run.py
# or
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- API base: `http://127.0.0.1:8000`
- Health: `GET /health`
- Docs: `http://127.0.0.1:8000/docs`

## Key endpoints (orientation)

- **Auth + OTP**
  - `POST /otp/generate` (dev returns OTP in response; remove in production)
  - `POST /auth/student/register`
  - `POST /auth/student/login`
  - `POST /auth/admin/register`
  - `POST /auth/admin/login`

- **Student book experience**
  - `GET /student/books/` (list)
  - `GET /student/books/search`
  - `GET /student/books/{id}/summary`
  - `GET /student/books/{id}/qa`
  - `GET /student/books/{id}/audio`

- **Student-triggered generation (public books only)**
  - `POST /student/generate/books/{id}/summary`
  - `POST /student/generate/books/{id}/qa`
  - `POST /student/generate/books/{id}/podcast`

- **RAG chat**
  - `POST /rag/books/{id}/query`
  - `GET /rag/books/{id}/index-status`
  - `POST /rag/books/{id}/reindex`
  - `DELETE /rag/books/{id}/index`

## Notes / gotchas

- **Embedding dimensions must match your stored vectors.**
  - If you change embedding models after indexing, old collections can fail at query-time.
  - Fix by calling `POST /rag/books/{id}/reindex` (or deleting the collection and reprocessing).

- **Secrets**
  - Don’t hardcode API keys in code or commit them in `.env.example`.
  - Use `.env` locally and environment variables in deployment.

## Documentation

- Setup: `docs/SETUP.md`
- Architecture + dataflows: `docs/ARCHITECTURE.md`
- Load testing: `docs/LOAD_TESTING.md`
- Deep dive (complexities): `docs/COMPLEXITIES.md`

---
