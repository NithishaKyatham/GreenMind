# GreenMind — Deployment Guide

This describes a realistic, low-cost deployment for a student project.
None of this has been executed by me — follow it locally and adjust for
whatever you actually provision.

## Recommended split
- **Backend + PostgreSQL**: Render, Railway, or Fly.io (all have free/cheap tiers).
- **Frontend**: Vercel or Netlify (static Vite build).
- **Model file**: too large for Git — host on Hugging Face Hub, S3, or a
  Render persistent disk, and download it at container build/start time.

## Backend (example: Render)
1. Push this repo to GitHub (model weights excluded via `.gitignore`).
2. New Render Web Service → connect repo → root directory `backend/`.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add a Render PostgreSQL instance; copy its connection string into
   `DATABASE_URL`.
6. Set all other env vars from `.env.example` (JWT_SECRET, WEATHER_API_KEY,
   AI_API_KEY, MODEL_PATH, ALLOW_MODEL_FALLBACK, BACKEND_CORS_ORIGINS —
   set this to your deployed frontend's URL).
7. If your trained model isn't in the repo, add a startup script that
   downloads it (e.g. from Hugging Face Hub) into `ml/models/` before
   `uvicorn` starts.

## Frontend (example: Vercel)
1. Import the repo, root directory `frontend/`.
2. Framework preset: Vite.
3. Build command: `npm run build`, output directory `dist`.
4. Env var: `VITE_API_BASE_URL=https://<your-backend-domain>/api`

## Database migrations
This project creates tables via `Base.metadata.create_all()` at startup for
development convenience. Real Alembic migrations are already set up in
`backend/database/migrations/` (initial schema in `versions/0001_initial_schema.py`):
```bash
cd backend
alembic upgrade head        # apply migrations
alembic revision --autogenerate -m "describe your change"   # after model changes
```
For a production deployment, remove the `create_all()` call in `app/main.py`
and rely on `alembic upgrade head` instead (run it as a release step / init container).

## Secrets checklist before going live
- [ ] `JWT_SECRET` is a long random value, not the example placeholder
- [ ] `.env` is not committed (verify with `git status`)
- [ ] `WEATHER_API_KEY` and `AI_API_KEY` (if used) are set as platform secrets, not in code
- [ ] `BACKEND_CORS_ORIGINS` is restricted to your actual frontend domain(s)
- [ ] `ALLOW_MODEL_FALLBACK=false` in production once a real trained model is deployed, so the app fails loudly instead of silently serving fallback predictions
