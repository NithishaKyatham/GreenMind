from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.prediction import DiseasePrediction
from app.models.recommendation import Recommendation


def create_prediction(
    db: Session, user_id: str, crop: str, image_path: str,
    disease: str, confidence: float, severity: str, is_fallback: bool,
    context_json: Optional[str] = None,
) -> DiseasePrediction:
    prediction = DiseasePrediction(
        user_id=user_id, crop=crop, image_path=image_path,
        disease=disease, confidence=confidence, severity=severity,
        is_fallback_prediction=is_fallback,
        context_json=context_json,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def attach_recommendation(db: Session, prediction_id: str, rec: dict) -> Recommendation:
    recommendation = Recommendation(
        prediction_id=prediction_id,
        treatment=rec["treatment"],
        fertilizer=rec.get("fertilizer"),
        pesticide_guidance=rec.get("pesticide_guidance"),
        prevention=rec.get("prevention"),
        crop_management=rec.get("crop_management"),
        monitoring_advice=rec.get("monitoring_advice"),
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return recommendation


def get_prediction_by_id(db: Session, prediction_id: str, user_id: str) -> Optional[DiseasePrediction]:
    return (
        db.query(DiseasePrediction)
        .filter(DiseasePrediction.id == prediction_id, DiseasePrediction.user_id == user_id)
        .first()
    )


def list_predictions_for_user(
    db: Session, user_id: str, crop: Optional[str] = None,
    date_from=None, date_to=None, sort_desc: bool = True, search: Optional[str] = None,
) -> List[DiseasePrediction]:
    query = db.query(DiseasePrediction).filter(DiseasePrediction.user_id == user_id)
    if crop:
        query = query.filter(DiseasePrediction.crop == crop)
    if search:
        query = query.filter(DiseasePrediction.disease.ilike(f"%{search}%"))
    if date_from:
        query = query.filter(DiseasePrediction.created_at >= date_from)
    if date_to:
        query = query.filter(DiseasePrediction.created_at <= date_to)
    query = query.order_by(desc(DiseasePrediction.created_at) if sort_desc else DiseasePrediction.created_at)
    return query.all()
