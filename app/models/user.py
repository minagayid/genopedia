"""User and revocable browser-session models."""
from datetime import datetime, timezone
import uuid
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def new_id() -> str:
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
    sessions: Mapped[list["AuthSession"]] = relationship(back_populates="user", cascade="all, delete-orphan", passive_deletes=True)

class AuthSession(Base):
    __tablename__ = "user_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    csrf_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    expires_at: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    user: Mapped[User] = relationship(back_populates="sessions")
