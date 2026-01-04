# LibraryAI — Student Portal

The Student Portal is the user-facing experience: browse books and use AI features (summary, Q&A, podcasts/audio, and RAG chat when indexed).

## Demo (student portal)

> TODO: Add student portal demo video here.
>
> - Video link: 
> - Or embed:
>
> ```html
> <!-- Paste your video embed (YouTube/Drive/etc.) here -->
> ```

## Pages

- `pages/login.html`
- `pages/register.html`
- `pages/dashboard.html`

## Backend dependency

Default backend base URL in scripts:
- `http://127.0.0.1:8000`

If you change the backend host/port, update `API_BASE_URL` in:
- `scripts/login.js`
- `scripts/register.js`
- `scripts/dashboard.js`

## Auth flow (OTP + JWT)

- Request OTP: `POST /otp/generate`
- Student register: `POST /auth/student/register`
- Student login: `POST /auth/student/login`

On success, the portal stores student session details (including JWT) in `localStorage` under `student`.

## Key student capabilities

- Browse/search books
- View summary / Q&A / audio (if available)
- Trigger on-demand generation for public books (depends on backend policy)
- Ask questions via RAG chat for indexed books

## Run

Use the root frontend instructions in `Frontend/README.md`.
