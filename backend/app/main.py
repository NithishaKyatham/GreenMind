"""
GreenMind FastAPI application entrypoint.
"""
import logging
import os

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.database import Base, engine
from app.api import auth, crops, disease, history, weather, chatbot, reports, admin, tts, xai
from app.ml import model_loader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("greenmind")

app = FastAPI(
    title="GreenMind API",
    description="AI-Powered Crop Disease Detection and Recommendation System",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    if settings.ENVIRONMENT.lower() == "production" and (
        settings.JWT_SECRET == "insecure-dev-secret-change-me" or len(settings.JWT_SECRET) < 32
    ):
        raise RuntimeError("Set JWT_SECRET to a random value of at least 32 characters in production.")

    # Create DB tables if they don't exist (dev convenience; use Alembic migrations in production)
    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    logger.info("GreenMind backend starting up | environment=%s", settings.ENVIRONMENT)

    if not os.path.exists(settings.MODEL_PATH):
        if settings.ALLOW_MODEL_FALLBACK:
            logger.warning(
                "No trained model found at %s — starting in DEVELOPMENT FALLBACK mode. "
                "Disease predictions will be clearly labeled as demo/fallback, not real AI output.",
                settings.MODEL_PATH,
            )
        else:
            raise RuntimeError(
                f"Model file not found at {settings.MODEL_PATH} and ALLOW_MODEL_FALLBACK=false. "
                "Train a model first (see ml/training/train.py) or set ALLOW_MODEL_FALLBACK=true."
            )
    else:
        logger.info("Trained model found at %s", settings.MODEL_PATH)

    model_loader.load_model()


# ---------- Global error handlers: never leak raw stack traces to the client ----------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Invalid request data", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error. Please try again later."},
    )


@app.get("/api/health", tags=["System"])
def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(crops.router, prefix=settings.API_PREFIX)
app.include_router(disease.router, prefix=settings.API_PREFIX)
app.include_router(xai.router, prefix=settings.API_PREFIX)
app.include_router(history.router, prefix=settings.API_PREFIX)
app.include_router(weather.router, prefix=settings.API_PREFIX)
app.include_router(chatbot.router, prefix=settings.API_PREFIX)
app.include_router(reports.router, prefix=settings.API_PREFIX)
app.include_router(admin.router, prefix=settings.API_PREFIX)
app.include_router(tts.router, prefix=settings.API_PREFIX)
# Note: there is no separate recommendations.router — recommendations are
# generated inline during /api/disease/predict and returned as part of the
# prediction response (see app/services/recommendation_service.py), since
# a recommendation only ever makes sense attached to a specific prediction.
