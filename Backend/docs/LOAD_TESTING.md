# Load Testing (Locust)

This backend includes a Locust client to pressure-test the API and specifically expose issues in the expensive paths (RAG + generation).

## Install Locust

```powershell
pip install locust
```

## Run

From `Backend/`:

```powershell
cd "D:\3Sem Minor\Backend"
locust -f .\locust\locustfile.py --host http://127.0.0.1:8000
```

Open the web UI:
- `http://127.0.0.1:8089`

## What it tests

The included tasks hit:

- `GET /` (sanity)
- `POST /rag/books/{id}/query` (hot path)
- `GET /student/books/{id}/summary|qa|audio`

## Interpreting failures

- 404s usually mean the random `book_id` doesn’t exist.
- 500s in RAG often mean:
  - book not indexed (empty collection)
  - Redis/LLM down
  - embedding dimension mismatch (if the embedding model was changed after indexing)
