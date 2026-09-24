from datetime import datetime
from pydantic import BaseModel


class ReportOut(BaseModel):
    id: str
    prediction_id: str
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True
