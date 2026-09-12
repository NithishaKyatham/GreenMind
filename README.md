# GreenMind
**AI-Powered Crop Disease Detection and Recommendation System for Sustainable Development**

## Status: functionally complete, running a real trained model

This has moved past scaffolding: a real EfficientNet-B0 model, trained on
the 38-class PlantVillage set, is integrated into the live prediction
path, and the core flow (register → login → upload → real prediction →
recommendation → history → PDF report) has actually been exercised — see
`backend/uploads/` and `backend/reports/` for evidence, and
`backend/.pytest_cache` shows all 15 backend tests passing.

**⚠️ Model accuracy caveat:** the trained model scores 99.61% on a
PlantVillage held-out test set (8,179 lab-captured images, 38 classes).
That is not the same as real-world field accuracy — see
`ml/MODEL_INFO.md` for the full explanation and per-class numbers. Real
farm photos will score lower.

**⚠️ Supported scope:** the model recognizes exactly 38 crop/disease
combinations across 14 crops (Apple, Blueberry, Cherry, Corn, Grape,
Orange, Peach, Bell Pepper, Potato, Raspberry, Soybean, Squash,
Strawberry, Tomato). It does not identify every crop or every disease —
unsupported images should (and are designed to) come back as
low-confidence rather than a wrong specific diagnosis.

### What's implemented
- FastAPI backend: JWT auth, PostgreSQL/SQLite, global error handling, structured logging
- Real ML inference: model loaded once at startup, EfficientNet-B0, 224×224 + ImageNet normalization, exact class-order match to training
- **Confidence threshold** (`CONFIDENCE_THRESHOLD`, default 0.60): below it, the API returns `status: "low_confidence"` with a safe generic response instead of a specific (possibly wrong) diagnosis — the model's guess is exposed only as an unconfirmed hint
- **Crop identification from the image itself**, not blindly trusted from the user's dropdown — a mismatch between what the user selected and what the model identified is surfaced back to them
- Recommendation engine covering all 38 trained classes (`backend/app/services/recommendation_rules.json`) — rules as data, not hardcoded in the frontend
- Weather (OpenWeatherMap, honest "unavailable" fallback), chatbot (real LLM call path + rule-based fallback), PDF reports, history search/filter/sort, admin dashboard
- Frontend: React + TS + Vite + Tailwind, all 15 pages, protected routes
- **Multilingual**: English, Telugu, Hindi, Tamil, Kannada, Marathi
- **Voice input/output**: browser-native Web Speech API in the chat assistant — no external service or key, degrades gracefully (mic button simply doesn't render) on unsupported browsers
- Alembic migrations, Docker Compose (Postgres + backend + frontend, with the model/uploads/reports correctly volume-mounted), pytest + vitest suites

### What's not done / known limitations
- Alembic's initial migration was written by hand (not `--autogenerate`) since I can't run Alembic in my sandbox — review it against your actual DB before relying on it in production.
- I could not execute anything in this session (no internet → no `pip`/`npm install`, no torch) — every change is syntax-checked (`py_compile`, JSON validation, YAML validation) but not execution-verified by me. You have working evidence from your own runs (tests passed, real predictions in `backend/uploads/`) — re-run after pulling this update and tell me what (if anything) broke.
- CORS origins and secrets are dev defaults — tighten before any real deployment (see `docs/DEPLOYMENT.md`).

## Quick start (local, no Docker)

```bash
# 1. Backend
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env
# edit ../.env: set USE_SQLITE=true for the quickest local start
# MODEL_PATH defaults to ../ml/models/crop_disease_model.pt (relative to backend/) — already correct for the trained model shipped in this repo
uvicorn app.main:app --reload
# -> API docs at http://localhost:8000/docs

# 2. Run tests
pytest tests/ -v

# 3. Frontend (separate terminal)
cd ../frontend
npm install
npm run dev
# -> http://localhost:5173

# 4. Frontend tests
npm run test
```

## Creating an admin user
```bash
cd backend
python ../scripts/create_admin.py --email you@example.com --name "Admin" --password "SecurePass123"
```

## Database migrations
Alembic is configured in `backend/database/migrations/`. Dev mode uses
`create_all()` at startup for convenience; for production run
`cd backend && alembic upgrade head` instead. See `docs/DEPLOYMENT.md`.

## Quick start (Docker)

```bash
cp .env.example .env   # fill in real secrets
docker-compose up --build
# backend:  http://localhost:8000/docs
# frontend: http://localhost:5173
```
The backend container gets `MODEL_PATH`, `UPLOAD_DIR`, and `REPORTS_DIR`
overridden to absolute container paths in `docker-compose.yml` (the `.env`
relative-path defaults assume running from `backend/` on the host and
would resolve to the wrong location inside the container).

## Project structure

```
greenmind/
├── frontend/          React + TS + Vite + Tailwind, i18n, voice hook
├── backend/           FastAPI app
│   ├── app/
│   │   ├── api/        route handlers per domain
│   │   ├── models/     SQLAlchemy ORM models
│   │   ├── schemas/    Pydantic request/response schemas
│   │   ├── services/   recommendation engine, weather, chatbot, reports
│   │   ├── repositories/  DB access layer
│   │   ├── core/       config, database, security, deps
│   │   └── ml/         model loader / predictor / preprocessing
│   ├── database/migrations/  Alembic
│   └── tests/
├── ml/
│   ├── models/          trained crop_disease_model.pt + evaluation artifacts
│   ├── training/         train.py, evaluate.py, prepare_dataset.py
│   ├── MODEL_INFO.md      accuracy, classes, confidence threshold, caveats
│   └── DATASET_SETUP.md
├── database/schema.sql   plain-SQL schema reference
├── docs/                 architecture, API docs, deployment, project plan
├── docker-compose.yml
├── .env.example
└── README.md
```

## Tech stack
Frontend: React, Vite, TypeScript, Tailwind CSS, React Router, Axios, Recharts, Web Speech API
Backend: FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL (SQLite dev fallback)
ML: PyTorch, torchvision, EfficientNet-B0 (trained, 38 classes), OpenCV, Pillow

## Important honesty notes
- No fake predictions, weather data, or accuracy numbers anywhere in this codebase.
- 99.61% is a PlantVillage test-set number, not a field-accuracy claim — see `ml/MODEL_INFO.md`.
- Low-confidence predictions never get a specific diagnosis or recommendation — they get a safe generic response, by design.
- The AI disclaimer is shown wherever a prediction appears:
  *"AI-generated guidance is for informational purposes. For severe crop damage or uncertain diagnosis, consult a qualified agricultural expert."*

## Authors
Final-year B.Tech CSE major project — GreenMind.
