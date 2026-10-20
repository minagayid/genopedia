"""Database engine and request-scoped sessions."""
from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import get_settings

def build_engine(database_url: str):
    options = {"pool_pre_ping": True}
    if database_url.startswith("sqlite:"):
        options["connect_args"] = {"check_same_thread": False}
    return create_engine(database_url, **options)

engine = build_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
