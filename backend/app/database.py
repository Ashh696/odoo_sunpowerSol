from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session, DeclarativeBase
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# SQLAlchemy 2.0 Base
class Base(DeclarativeBase):
    pass

# Engine creation with pool settings and 3-second connection timeout
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG,
    connect_args={"connect_timeout": 3},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session per request.
    Closes the session after request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
