from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class RecommendationOut(BaseModel):
    treatment: str
    fertilizer: Optional[str] = None
    pesticide_guidance: Optional[str] = None
    prevention: Optional[str] = None
    crop_management: Optional[str] = None
    monitoring_advice: Optional[str] = None

    class Config:
        from_attributes = True


class PredictionContextOut(BaseModel):
    season: Optional[str] = None
    region: Optional[str] = None
    crop_stage: Optional[str] = None
    soil_info: Optional[str] = None
    weather: Optional[dict] = None


class PredictionOut(BaseModel):
    id: str
    crop: str
    disease: str
    confidence: float
    severity: str
    status: str  # "confident" | "low_confidence" | "fallback"
    description: str
    is_fallback_prediction: bool
    disclaimer: str
    image_path: str
    created_at: datetime
    recommendation: Optional[RecommendationOut] = None
    # Only populated when status == "low_confidence": the model's best guess,
    # shown as a soft hint, never as a confirmed diagnosis.
    possible_disease: Optional[str] = None
    crop_mismatch_note: Optional[str] = None
    context: Optional[PredictionContextOut] = None

    class Config:
        from_attributes = True


class PredictionHistoryItem(BaseModel):
    id: str
    crop: str
    disease: str
    confidence: float
    severity: str
    created_at: datetime

    class Config:
        from_attributes = True
