# Backend Architecture

This backend is split by responsibility (routes → services → models) and combines classic LMS flows with AI/RAG subsystems.

## Runtime components

- **FastAPI**: request routing, validation, middleware
- **MySQL**: core data persistence
- **Redis**: caching layer for expensive generation + RAG
- **ChromaDB (local persistence)**: vector index per book under `static/vectordb/`
- **AI providers**:
  - Hugging Face Inference API (summary/Q&A/podcast script)
  - Gemini via LangChain Google GenAI (RAG answers)

## Request flow (RAG)

1. `POST /rag/books/{book_id}/query`
2. Validate book exists in MySQL (`books` table)
3. Build a cache key from `(book_id, question, num_chunks)`
4. If cache hit in Redis → return cached result
5. Load Chroma collection `book_{book_id}` from `static/vectordb/`
6. Retrieve chunks using **MMR** for diversity
7. Feed context + question into Gemini (LangChain chain)
8. Return answer + sources; write to Redis cache

## Request flow (student-triggered generation)

1. Student calls `/student/generate/books/{id}/summary|qa|podcast`
2. Check cache → check DB → enforce `is_public == 1`
3. Generate content once (first request)
4. Persist into `static_content` table
5. Cache the result in Redis and invalidate related admin caches

## Data model highlights

- `Books`:
  - inventory (`total_copies`, `available_copies`)
  - governance (`is_public`) to control student-triggered generation
  - AI readiness (`rag_indexed`) to track whether chat is available
  - categorization via a many-to-many join table (`book_categories`)

- `Borrow`:
  - lifecycle status (`ACTIVE`, `RETURNED`, `OVERDUE`)
  - due date handling and fine calculation

## Performance tooling

- Targeted request profiling via **cProfile middleware** (only the RAG query endpoint)
- Load testing via Locust (`locust/locustfile.py`)

## Known “real-world” edge case

- Embedding model changes can cause **vector dimension mismatches** between stored collections and query embeddings.
- Fix: reindex affected books via `POST /rag/books/{book_id}/reindex`.
