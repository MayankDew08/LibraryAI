# Backend Setup

This backend expects three main runtime dependencies:

- **MySQL** (primary relational datastore)
- **Redis** (caching for AI and RAG)
- **Outbound network access** (optional but recommended): SendGrid + Hugging Face + Gemini

## 1) Python environment

```powershell
cd "D:\3Sem Minor\Backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Environment variables

Create `.env`:

```powershell
Copy-Item .env.example .env
```

Required values:

- `SQLALCHEMY_DATABASE_URL`
- `SECRET_KEY`

Required for full functionality:

- `HUGGINGFACE_API_TOKEN` (on-demand summary/Q&A/podcast script)
- `GEMINI_API_KEY` (RAG answer generation via LangChain Google GenAI)
- `SENDGRID_API_KEY` + `FROM_EMAIL` (OTP emails + borrow notifications)

## 3) MySQL

- Ensure MySQL is running
- Create a database (example): `library_db`
- Update `SQLALCHEMY_DATABASE_URL` accordingly

This repo currently does not ship with a single “one-click migration” script; the models are defined under `app/models/`.

## 4) Redis

The code uses Redis on `localhost:6379` by default.

- Windows: run Redis via WSL, Docker, or a local Redis-compatible service.
- If Redis is not running, caching will fail and expensive endpoints will be slower.

## 5) Start the server

```powershell
python run.py
```

Swagger UI:
- `http://127.0.0.1:8000/docs`

## 6) Static storage

The backend mounts `Backend/static/` at `/static`.

- PDFs: `static/pdfs/`
- Covers: `static/covers/`
- Generated audio: `static/podcasts/`
- Vector DB: `static/vectordb/` (Chroma persistence)
