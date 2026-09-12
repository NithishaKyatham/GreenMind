from sqlalchemy.orm import Session
from app.models.report import Report


def create_report(db: Session, user_id: str, prediction_id: str, file_path: str) -> Report:
    report = Report(user_id=user_id, prediction_id=prediction_id, file_path=file_path)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
