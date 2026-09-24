from datetime import datetime

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import gen_uuid


class DiseasePrediction(Base):
    __tablename__ = "disease_predictions"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    crop = Column(String(100), nullable=False)
    image_path = Column(String(500), nullable=False)
    disease = Column(String(150), nullable=False)
    confidence = Column(Float, nullable=False)  # 0.0 - 1.0
    severity = Column(String(20), nullable=False)  # Low / Medium / High
    is_fallback_prediction = Column(Boolean, default=False, nullable=False)  # dev-mode flag
    context_json = Column(String(4000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="predictions")
    recommendation = relationship(
        "Recommendation", back_populates="prediction", uselist=False, cascade="all, delete-orphan"
    )
    reports = relationship("Report", back_populates="prediction", cascade="all, delete-orphan")
