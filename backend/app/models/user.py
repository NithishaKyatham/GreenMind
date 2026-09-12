from datetime import datetime

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import gen_uuid


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    preferred_language = Column(String(10), default="en", nullable=False)
    location = Column(String(255), nullable=True)  # village/district/state/country combined
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    predictions = relationship("DiseasePrediction", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
