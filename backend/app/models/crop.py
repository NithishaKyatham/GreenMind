from sqlalchemy import Column, String

from app.core.database import Base
from app.models.base import gen_uuid


class Crop(Base):
    """Reference table of supported crops (Tomato, Potato, Maize, etc.)."""
    __tablename__ = "crops"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(100), unique=True, nullable=False)
    display_name_en = Column(String(100), nullable=False)
    display_name_te = Column(String(100), nullable=True)
    display_name_hi = Column(String(100), nullable=True)
