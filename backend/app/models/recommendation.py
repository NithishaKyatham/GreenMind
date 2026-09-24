from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import gen_uuid


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    prediction_id = Column(String(36), ForeignKey("disease_predictions.id"), nullable=False, unique=True)
    treatment = Column(Text, nullable=False)
    fertilizer = Column(Text, nullable=True)
    pesticide_guidance = Column(Text, nullable=True)
    prevention = Column(Text, nullable=True)
    crop_management = Column(Text, nullable=True)
    monitoring_advice = Column(Text, nullable=True)

    prediction = relationship("DiseasePrediction", back_populates="recommendation")
