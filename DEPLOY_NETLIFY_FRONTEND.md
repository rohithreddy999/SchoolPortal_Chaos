# Netlify Frontend Deployment

Netlify can host the `frontend/` React app, but it does **not** run the FastAPI backend in `backend/`.

Use Netlify only if:

- the frontend is deployed on Netlify
- the backend is deployed somewhere else
- `VITE_API_URL` is set in Netlify to that backend URL, for example:
  - `https://your-backend.example/api`

## What is already fixed in this repo

- Frontend file imports already match the actual file casing on disk.
- The frontend API fallback is already production-safe and defaults to `/api`, not `localhost`.
- A checked-in `netlify.toml` is now included so Netlify builds the `frontend/` workspace correctly.

## Files

- Netlify config: `netlify.toml`
- Frontend build root: `frontend/`
- Frontend output: `frontend/dist`

## Required Netlify setting

In the Netlify site environment variables, set:

```text
VITE_API_URL=https://your-backend.example/api
```

If you do **not** set this, the frontend will call `/api` on the Netlify domain itself, and those requests will fail unless you separately proxy `/api` there.

## Recommended backend hosts for this project

- Oracle Cloud Always Free VM
- Render
- Railway
- Fly.io

For this specific project, the best zero-cost full deployment remains the Oracle VM path documented in `DEPLOY_ORACLE_FREE.md`.
