"""
Import all models here so Base.metadata.create_all() / Alembic can discover them.
"""
from app.models.user import User          # noqa: F401
from app.models.crop import Crop          # noqa: F401
from app.models.prediction import DiseasePrediction   # noqa: F401
from app.models.recommendation import Recommendation  # noqa: F401
from app.models.weather import WeatherRecord           # noqa: F401
from app.models.chat import ChatMessage                # noqa: F401
from app.models.report import Report                    # noqa: F401
