from pydantic import BaseModel, Field


class ExplanationSegment(BaseModel):
    segment_id: int
    weight: float
    supports_prediction: bool


class ExplanationOut(BaseModel):
    prediction_id: str
    target_class: str
    target_label: str
    method: str = Field(default="lime")
    segments: list[ExplanationSegment]
    explanation_image: str
    disclaimer: str
