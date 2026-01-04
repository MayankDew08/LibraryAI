# Backend Complexities (What I Built and How Far It’s Pushed)

This document is a detailed breakdown of the backend infrastructure and engineering complexity in this project. It’s written to communicate *why* the backend is not “just CRUD” and what real-world system concerns were implemented.

## 1) System scope (beyond CRUD)

The backend combines classic Library Management System workflows with AI-driven study features:

- Inventory + cataloging (books, categories, static assets)
- Borrow/return lifecycle with due dates and fine calculation
- OTP-based flows for user/admin registration + login
- JWT authentication for protected routes
- On-demand AI generation (summary, Q&A, podcast script, offline TTS audio)
- RAG chat over book PDFs with a persistent vector database
- Caching + profiling + load testing to validate performance and reliability

## 2) Security model (OTP + JWT + role boundaries)

### OTP-first authentication
- Users generate an OTP via `POST /otp/generate`.
- OTP is verified during registration and login.
- OTP has expiry and attempt limits (defense against repeated guessing).

> Development note: OTP endpoints currently return the OTP in API responses for convenience. That must be removed for production.

### Password security
- Passwords are hashed using bcrypt before storage.

### JWT-based authorization
- After successful register/login, the backend issues a **bearer JWT**.
- Tokens have an expiry (configured via environment variables).
- Protected routes use dependency injection to enforce authentication.

### Role-based access control (RBAC)
- Admin-only endpoints are guarded by an admin token dependency (example: admin books management, borrow verification endpoints).
- Student flows enforce student role and additional policies (example: student-triggered generation only when the book is public).

## 3) Data integrity and relational modeling (MySQL + SQLAlchemy)

The core system state lives in MySQL (SQLAlchemy models). This supports real library logic with correctness constraints:

- **Books** store inventory counts and guard rails:
  - `total_copies >= 0`
  - `available_copies >= 0`
  - `available_copies <= total_copies`
- **Borrow records** track lifecycle state:
  - Status enum (`ACTIVE`, `RETURNED`, `OVERDUE`)
  - Due date and fine calculation (late returns)
- **Categories** are modeled as a proper many-to-many relationship (book ↔ category join table)
- **Static content** is persisted in the database so generation is done once and reused

This isn’t just a data dump—constraints enforce correctness at the DB layer, which is closer to real production behavior.

## 4) On-demand AI content generation subsystem

There are two different patterns:

1. **Admin-driven generation**
   - Admin endpoints can create a book and run everything automatically (upload → generate → store).

2. **Student-triggered generation for public books**
   - Students can request generation only when `is_public == 1`.
   - First request generates; subsequent requests reuse stored content.

Generated artifacts:
- Summary text
- Q&A pairs (structured)
- Podcast script
- Audio file generated offline via TTS

Key complexity here is orchestrating:
- policy checks (public vs confidential)
- persistence (store once)
- caching/invalidation (avoid repeated cost)

## 5) RAG subsystem (PDF → embeddings → retrieval → answer)

This project includes a complete RAG pipeline with persistent indexing.

### RAG ingestion pipeline
- Load PDF pages
- Clean noise (headers/footers/metadata)
- Chunk content with overlap (tuned for retrieval quality)
- Deduplicate chunks (hash-based to remove exact duplicates)
- Compute embeddings
- Store vectors in **ChromaDB** (persisted locally)

### Index topology
- Each book is indexed into its own collection: `book_{book_id}`.
- Collections persist under `static/vectordb/`.

### Retrieval strategy
- Uses **MMR (Maximal Marginal Relevance)** retrieval to balance:
  - relevance to the question
  - diversity across retrieved chunks

This avoids retrieving multiple near-identical chunks and improves answer coverage.

### Answer generation
- Retrieved context is fed into an LLM prompt to generate a teaching-style answer.
- System returns answer + sources used.

## 6) Caching strategy (Redis)

The backend includes Redis caching because AI calls are expensive and slow compared to standard CRUD.

- RAG queries cache results by a stable key derived from:
  - `book_id`, `question`, `num_chunks`
- On-demand generation caches outputs and also invalidates admin caches when students generate content

This is an explicit optimization step that’s often skipped in student projects.

## 7) Performance engineering (profiling built-in)

RAG queries are the hottest, most expensive path.

This backend includes targeted profiling:
- A middleware that runs **cProfile** only for `POST /rag/books/{id}/query`
- Profiles are written into the `profiles/` directory

This is a practical tool to measure where time is spent inside PDF retrieval + LLM calls under real traffic.

## 8) Load testing (Locust)

There is a Locust client to push the backend under concurrent load.

It exercises:
- basic health/root requests
- RAG queries
- student endpoints for summary/Q&A/audio

This helps surface issues that don’t show up in single-user testing:
- 404s from missing IDs
- slow paths that require caching
- RAG failures due to indexing state

## 9) Operational realism

The backend includes pieces that model real ops concerns:

- **Static file serving** for PDFs/covers/audio
- **Email delivery** via SendGrid for OTP and notifications
- Environment-driven config via `.env`

## 10) Known complex failure mode (real-world class)

### Embedding dimension mismatch
If the embedding model changes after books were indexed, existing collections may contain vectors with a different dimension than the current embedding model. That can cause RAG query failures at runtime.

Mitigation:
- Reindex affected books (`POST /rag/books/{book_id}/reindex`) or delete the index and rebuild.

This is a real RAG operational issue and is part of what makes the system non-trivial.

## 11) What “pushed” means in this backend

This backend was pushed beyond a typical course project by:

- combining classic transactional flows (borrowing, inventory) with AI pipelines
- persisting AI outputs and indexing state (not regenerating every time)
- implementing multi-layer caching
- adding targeted profiling for the hot endpoint
- validating behavior under load with Locust
- enforcing security boundaries (OTP + JWT + RBAC)
- storing vectors persistently (Chroma) and treating indexing as part of the backend lifecycle
