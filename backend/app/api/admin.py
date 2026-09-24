"""
Admin-only endpoints. Never exposes password hashes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.user import User
from app.models.prediction import DiseasePrediction
from app.schemas.admin import AdminStatsOut, DiseaseCount, CropCount, AdminUserOut

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=AdminStatsOut)
def get_stats(db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_predictions = db.query(func.count(DiseasePrediction.id)).scalar() or 0

    disease_rows = (
        db.query(DiseasePrediction.disease, func.count(DiseasePrediction.id).label("cnt"))
        .group_by(DiseasePrediction.disease)
        .order_by(desc("cnt"))
        .limit(10)
        .all()
    )
    crop_rows = (
        db.query(DiseasePrediction.crop, func.count(DiseasePrediction.id).label("cnt"))
        .group_by(DiseasePrediction.crop)
        .order_by(desc("cnt"))
        .limit(10)
        .all()
    )

    return AdminStatsOut(
        total_users=total_users,
        total_predictions=total_predictions,
        most_detected_diseases=[DiseaseCount(disease=d, count=c) for d, c in disease_rows],
        most_analyzed_crops=[CropCount(crop=cr, count=c) for cr, c in crop_rows],
    )


@router.get("/users", response_model=list[AdminUserOut])
def list_users(db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    rows = (
        db.query(User, func.count(DiseasePrediction.id).label("pred_count"))
        .outerjoin(DiseasePrediction, DiseasePrediction.user_id == User.id)
        .group_by(User.id)
        .all()
    )
    return [
        AdminUserOut(id=u.id, name=u.name, email=u.email, is_active=u.is_active, prediction_count=cnt)
        for u, cnt in rows
    ]


@router.get("/predictions/recent", response_model=list)
def recent_predictions(db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    rows = (
        db.query(DiseasePrediction)
        .order_by(desc(DiseasePrediction.created_at))
        .limit(20)
        .all()
    )
    return [
        {
            "id": p.id, "user_id": p.user_id, "crop": p.crop, "disease": p.disease,
            "confidence": p.confidence, "severity": p.severity, "created_at": p.created_at,
        }
        for p in rows
    ]
