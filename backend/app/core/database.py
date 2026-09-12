"""
SQLAlchemy engine + session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.USE_SQLITE else {}

engine_kwargs = {
    "connect_args": connect_args,
    "pool_pre_ping": True,
}

# SQLite test/dev databases should not keep pooled file handles open.
if settings.USE_SQLITE:
    engine_kwargs["poolclass"] = NullPool

engine = create_engine(
    settings.sqlalchemy_database_url,
    **engine_kwargs,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()