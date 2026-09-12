# GreenMind — Phased Implementation Plan

| Phase | Scope | Status |
|---|---|---|
| 1 | Project setup: structure, config, docker-compose, .env, README | ✅ Done |
| 2 | Database + authentication (models, JWT, bcrypt, tests) | ✅ Done (this phase merged with 1) |
| 3 | Remaining backend APIs: crops, disease, recommendations, history | ⏳ Next |
| 4 | Frontend: routing, pages, auth context, API client, i18n scaffold | ⏳ Pending |
| 5 | ML pipeline: dataset prep, augmentation, training script | ⏳ Pending |
| 6 | Prediction integration: model_loader, predictor, /api/disease/predict | ⏳ Pending |
| 7 | Recommendation engine (rules-driven, JSON/DB-backed) | ⏳ Pending |
| 8 | Weather integration (OpenWeatherMap, caching, fallback) | ⏳ Pending |
| 9 | Chatbot: GreenMind Assistant (context-aware, LLM + rule-based fallback) | ⏳ Pending |
| 10 | Reports (PDF via ReportLab) + history search/filter/sort | ⏳ Pending |
| 11 | Admin dashboard: stats, user management, charts | ⏳ Pending |
| 12 | Testing: expanded pytest (recommendations, weather honesty, reports) + Vitest | ✅ Done |
| 13 | Docker: backend + frontend Dockerfiles, docker-compose, .dockerignore | ✅ Done |
| 14 | Deployment docs, Alembic migrations, admin seed script | ✅ Done |

## Risks & limitations identified up front
- **No real accuracy claims until a model is actually trained** on a real
  dataset split — training compute/GPU access is the main external
  dependency and is the student's responsibility to run (Colab / Kaggle
  free GPU tier is the realistic option).
- **Weather API key** (OpenWeatherMap free tier) must be obtained by the
  student — code is written against it but untested without a live key.
- **Chatbot** can either call a real LLM API (needs `AI_API_KEY`) or run in
  a rule-based fallback mode — both paths are real, neither is faked.
- Every phase after this one will be delivered as its own reviewable chunk,
  not one giant undifferentiated code drop.
