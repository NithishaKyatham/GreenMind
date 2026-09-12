from typing import List
from pydantic import BaseModel


class DiseaseCount(BaseModel):
    disease: str
    count: int


class CropCount(BaseModel):
    crop: str
    count: int


class AdminStatsOut(BaseModel):
    total_users: int
    total_predictions: int
    most_detected_diseases: List[DiseaseCount]
    most_analyzed_crops: List[CropCount]


class AdminUserOut(BaseModel):
    id: str
    name: str
    email: str
    is_active: bool
    prediction_count: int

    class Config:
        from_attributes = True
