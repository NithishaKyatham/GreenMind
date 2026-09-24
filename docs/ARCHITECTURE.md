# GreenMind — Architecture

```
Farmer
  |
  v
React + TypeScript Frontend (Vite, Tailwind)
  |  (REST, JWT bearer token)
  v
FastAPI Backend  (/api/*)
  |
  |-- Auth (JWT, bcrypt password hashing)
  |
  +-- api/crops.py            -> Crop reference data
  +-- api/disease.py          -> Image upload -> ML inference -> prediction record
  +-- api/recommendations.py  -> Rule-based recommendation engine
  +-- api/weather.py          -> OpenWeatherMap integration (cached in DB)
  +-- api/chatbot.py          -> GreenMind Assistant (LLM or rule-based fallback)
  +-- api/reports.py          -> PDF report generation (ReportLab)
  +-- api/history.py          -> Prediction history, search/filter/sort
  +-- api/admin.py            -> Admin-only stats & user management
  |
  v
SQLAlchemy ORM
  |
  v
PostgreSQL  (SQLite fallback for local dev)

Separately:
ml/  -- training pipeline (PyTorch, EfficientNet-B0 transfer learning)
     -- produces ml/models/crop_disease_model.pt
     -- backend/app/ml/model_loader.py loads this at startup
     -- if absent, backend runs in labeled DEVELOPMENT FALLBACK mode
```

## Why these choices

- **FastAPI over Django**: async-friendly, auto-generated OpenAPI docs
  (`/docs`, `/redoc`), and Pydantic validation fits an ML-serving API well.
- **PostgreSQL primary / SQLite fallback**: `USE_SQLITE=true` env var swaps
  the SQLAlchemy engine with zero code changes, so a contributor without
  Docker/Postgres installed can still run the app.
- **EfficientNet-B0 (transfer learning)** chosen over training from scratch:
  best accuracy-per-compute tradeoff for a leaf-image classification task
  with a modest dataset, and it's small enough to serve on CPU without a GPU
  in production — a realistic constraint for a student/early-stage deployment.
- **JWT stateless auth**: simple to reason about, no server-side session
  store needed; refresh tokens rotate access tokens without re-login.
- **Recommendation engine as data, not code**: `recommendation_rules.json`
  (or a DB table) maps (crop, disease, severity) -> guidance text, so
  agricultural content can be updated without redeploying the app, and it's
  never fabricated per-request by an LLM.

## Known limitations (documented, not hidden)

- No real-time push notifications (out of scope for this version).
- Chatbot's LLM mode requires `AI_API_KEY`; without it, falls back to a
  rule-based agricultural FAQ responder — clearly labeled in the UI as
  "Basic Assistant Mode" rather than pretending to be the full AI assistant.
- Model accuracy is whatever the trained model actually achieves on the
  held-out test set — reported from `ml/training/evaluate.py` output, never
  invented. Until training happens, the API serves clearly-labeled fallback
  predictions.
