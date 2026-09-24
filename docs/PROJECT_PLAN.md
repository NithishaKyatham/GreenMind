# GreenMind Project Status and Technical Plan

## Problem statement and objectives

GreenMind helps farmers identify leaf diseases from a crop image and receive
careful, crop-specific guidance. It aims to make early disease information,
weather context, history, and downloadable reports easier to access. It is an
advisory system: uncertain results must not be treated as a diagnosis.

## Current implementation status

| Area | Status | Notes |
|---|---|---|
| Project configuration, Docker, and local setup | Implemented | Production secrets must be supplied through `.env`. |
| Database, JWT authentication, and roles | Implemented | PostgreSQL is the deployment target; SQLite is supported for development/tests. |
| Crop catalogue, prediction, recommendations, history | Implemented | Private data is filtered by authenticated user. |
| React farmer portal and admin dashboard | Implemented | Responsive pages, protected routes, and API client are present. |
| PlantVillage ML pipeline and live inference | Implemented | EfficientNet-B0, 38 classes, confidence safety handling. |
| Weather and chatbot | Implemented with external dependency | Weather needs an OpenWeatherMap key; chatbot has a labelled rule-based fallback if no AI key is configured. |
| Reports, tests, migrations, deployment documentation | Implemented | Must be re-verified in the intended deployment environment. |

## System architecture

The React/Vite frontend sends authenticated requests to the FastAPI backend.
FastAPI validates uploads, calls the PyTorch inference layer, stores a
prediction and rule-driven recommendation through SQLAlchemy, and returns a
safe response. PostgreSQL is used in Docker/production and SQLite provides a
local development fallback. Uploaded images and generated PDFs are stored on
mounted volumes in Docker.

## Methodology and AI/ML model

The model is an EfficientNet-B0 classifier trained on the PlantVillage
38-class dataset across 14 supported crops. Images are converted to RGB,
resized to 224x224, converted to tensors, and normalized with ImageNet mean
and standard deviation before inference. The class order is loaded from
`ml/models/class_names.json` alongside `crop_disease_model.pt`.

The packaged evaluation reports a 99.61% held-out PlantVillage test accuracy.
This is a lab-image benchmark, not a real-field accuracy claim. Field photos,
unsupported crops, and poor-quality images can produce lower confidence. A
result below the configured threshold or a selected-crop/model-crop mismatch
is presented as uncertain and receives generic safe guidance instead of a
disease-specific treatment.

## Backend and API flow

Important endpoint groups are `/api/auth`, `/api/crops`, `/api/disease`,
`/api/history`, `/api/reports`, `/api/weather`, `/api/chatbot`, and
`/api/admin`. The normal flow is register -> login -> Bearer access token ->
image upload -> inference -> recommendation persistence -> history/report.
Image and report retrieval both enforce user ownership. Admin endpoints require
an authenticated administrator.

## Frontend and user-facing features

The frontend includes landing, registration, login, dashboard, crop upload,
prediction result, history/detail, weather, chat, profile, and admin pages.
Farmer-facing UI supports English, Telugu, Hindi, Tamil, Kannada, Malayalam,
Marathi, Bengali, Gujarati, and Punjabi.
Browser Web Speech support is optional and degrades gracefully on unsupported
browsers.

## Database, migrations, and deployment

The initial Alembic migration creates users, crops, predictions,
recommendations, weather records, chats, and reports, including key user and
time indexes. Run `alembic upgrade head` against a clean production database;
the app's `create_all()` startup behavior is for local development only.

Docker Compose starts PostgreSQL, backend, and frontend. Set strong values for
`POSTGRES_PASSWORD`, `DATABASE_URL`, and `JWT_SECRET` in `.env`; set allowed
frontend origins in `BACKEND_CORS_ORIGINS`. The backend rejects the built-in
development JWT secret when `ENVIRONMENT=production`.

## Testing and known limitations

Backend pytest covers authentication, predictions, confidence/crop safety,
history ownership, reports, weather, chatbot, admin access, and agent tools.
Frontend Vitest covers route protection, localisation, speech services, and
key page behavior. Run both suites and a frontend production build after each
release.

External integrations cannot be fully verified without valid credentials and
network access. The model should be validated with representative local farm
photos before claiming real-world accuracy. Future work includes field-data
evaluation, translated recommendation content, token revocation, and a
reviewed production migration workflow.
