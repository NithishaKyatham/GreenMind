import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.config import settings
from app.models.user import User
from app.repositories.prediction_repository import get_prediction_by_id
from app.repositories.report_repository import create_report
from app.services.report_service import generate_prediction_report
from app.schemas.report import ReportOut

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate/{prediction_id}", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def generate_report(
    prediction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prediction = get_prediction_by_id(db, prediction_id, current_user.id)
    if not prediction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")

    filepath = generate_prediction_report(prediction, current_user, settings.REPORTS_DIR)
    report = create_report(db, current_user.id, prediction_id, filepath)
    return report


@router.get("/download/{report_id}")
def download_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.report import Report
    report = db.query(Report).filter(Report.id == report_id, Report.user_id == current_user.id).first()
    if not report or not os.path.exists(report.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return FileResponse(report.file_path, media_type="application/pdf", filename=os.path.basename(report.file_path))
