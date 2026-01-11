# LibraryAI — Library Management + AI Study Assistant (RAG)

LibraryAI is a production-minded Library Management System that goes beyond CRUD: it combines a traditional LMS backend (catalog, borrowing, roles, JWT auth) with an AI layer that can generate summaries/Q&A/audio and run Retrieval-Augmented Generation (RAG) chat over uploaded book PDFs.

What makes this project showcase-ready is the engineering focus: the system includes a full document ingestion + vector store pipeline, retrieval quality techniques (MMR), caching for expensive AI paths, and load testing/profiling to validate performance under real traffic.

## What you can do

**Student experience**
- Browse/search the catalog
- Read AI-generated summary and Q&A (when available)
- Listen to generated audio/podcast outputs (when available)
- Ask questions via RAG chat for indexed books
- Trigger on-demand generation for public books (policy enforced by backend)

**Admin experience**
- Upload/manage books (PDF + cover, categories)
- Trigger indexing/re-indexing for RAG
- Manage content workflows and catalog quality

## Why it’s unique (for a student project)

- **End-to-end RAG system**: PDF → clean text → chunking → embeddings → persistent ChromaDB → retrieval → Gemini answer generation
- **Retrieval quality**: uses **MMR (Maximal Marginal Relevance)** to improve coverage and reduce redundant chunks
- **Performance engineering**: Redis caching for expensive RAG/generation calls, targeted profiling of the slow path, and Locust load testing
- **Operational realism**: JWT + OTP flows, role-aware authorization, persistent static assets (PDFs/covers/audio), and environment-based configuration

## Tech stack

- **Backend**: FastAPI, SQLAlchemy, MySQL, Redis, ChromaDB (persistent vector store)
- **AI**: Gemini (answering/generation), embeddings + vector retrieval
- **Frontend**: static HTML/CSS/JavaScript (no build step)
- **Testing/Perf**: Locust, profiling tools (backend)

## Repository layout

```text
Backend/     # FastAPI API, DB models, RAG pipeline, caching, tests, docs
Frontend/    # Static student + admin portals
```

## Run locally

### 1) Backend (API)

Requirements:
- Python 3.x
- MySQL running and configured
- Redis running (default: localhost:6379)

```powershell
cd "D:\3Sem Minor\Backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# copy env and edit values as needed
Copy-Item .env.example .env

# run
python run.py
```

Backend:
- API: `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`

### 2) Frontend (UI)

The frontend is static. Serve it locally:

```powershell
cd "D:\3Sem Minor\Frontend"
python -m http.server 5500
```

Then open:
- `http://127.0.0.1:5500/`

If you change the backend host/port, update `API_BASE_URL` in the frontend scripts (see Frontend README).

## Documentation

- Backend docs live in `Backend/docs/` (setup, architecture, load testing)
- Backend README includes endpoint orientation and system details

## Screenshots / demo

> Add a short demo video and a few screenshots here for GitHub.

---

If you want, I can also add a minimal root-level “one command” dev script (Windows-friendly) that boots Redis/MySQL checks + backend + frontend server in a predictable order.
