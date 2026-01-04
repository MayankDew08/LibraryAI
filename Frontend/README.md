# LibraryAI — Frontend

See the project overview in the repository root: `README.md`.

A clean, static (no-build) frontend for the LibraryAI project.

- Landing page: role selection (Student/Admin)
- Student portal: browse books, AI summaries/Q&A, audio/podcasts, and RAG chat
- Admin portal: upload/manage books, trigger indexing/generation workflows

This frontend is built using plain **HTML/CSS/JavaScript** and talks to the FastAPI backend over HTTP.

## Demo (overall)

> TODO: Add overall frontend demo video here.
>
> - Video link: 
> - Or embed:
>
> ```html
> <!-- Paste your video embed (YouTube/Drive/etc.) here -->
> ```

## Project structure

```text
Frontend/
  index.html
  shared/
    styles/
    scripts/
    assets/

  admin/
    pages/
    scripts/
    styles/

  student/
    pages/
    scripts/
    styles/
```

## Backend dependency

By default, the frontend calls the backend at:

- `http://127.0.0.1:8000`

If you change the backend host/port, update `API_BASE_URL` inside the portal scripts:

- `admin/scripts/login.js`
- `admin/scripts/register.js`
- `admin/scripts/dashboard.js`
- `student/scripts/login.js`
- `student/scripts/register.js`
- `student/scripts/dashboard.js`

## Run locally

Because this is a static frontend, you can run it in two ways.

### Option A: Open directly (quickest)

- Open `Frontend/index.html` in your browser.

### Option B: Serve via a local static server (recommended)

Some browser features work more reliably when served over HTTP.

From the `Frontend/` directory:

```powershell
cd "D:\3Sem Minor\Frontend"
python -m http.server 5500
```

Then open:
- `http://127.0.0.1:5500/`

Tooling/runtime notes are listed in `requirements.txt`.

## Portals

- Admin portal docs: `admin/README.md`
- Student portal docs: `student/README.md`

## Notes

- Authentication state is stored in `localStorage` (student/admin sessions are separated).
- OTP is requested from the backend and used during login/register flows.
