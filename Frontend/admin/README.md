# LibraryAI — Admin Portal

The Admin Portal is used to manage the library catalog and power the AI workflows behind the scenes.

## Demo (admin portal)

> TODO: Add admin portal demo video here.
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
- Admin register: `POST /auth/admin/register`
- Admin login: `POST /auth/admin/login`

On success, the portal stores admin session details (including JWT) in `localStorage` under `admin`.

## Key admin capabilities

- Book upload/creation (PDF + cover)
- Category assignment
- Trigger RAG indexing and content generation workflows (depending on the endpoint used)

## Run

Use the root frontend instructions in `Frontend/README.md`.
