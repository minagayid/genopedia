from datetime import datetime,timezone
from sqlalchemy import Boolean,DateTime,ForeignKey,Integer,String,Text,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column,relationship
from .database import Base
def utcnow():return datetime.now(timezone.utc)
class User(Base):
 __tablename__="users"
 id:Mapped[int]=mapped_column(Integer,primary_key=True); email:Mapped[str]=mapped_column(String(320),unique=True,index=True,nullable=False); full_name:Mapped[str|None]=mapped_column(String(120)); password_hash:Mapped[str|None]=mapped_column(String(512)); email_verified:Mapped[bool]=mapped_column(Boolean,default=False,nullable=False); is_active:Mapped[bool]=mapped_column(Boolean,default=True,nullable=False); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow,nullable=False); updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow,onupdate=utcnow,nullable=False)
 refresh_sessions:Mapped[list["RefreshSession"]]=relationship(back_populates="user",cascade="all, delete-orphan")
class RefreshSession(Base):
 __tablename__="refresh_sessions"; __table_args__=(UniqueConstraint("token_hash",name="uq_refresh_token_hash"),)
 id:Mapped[int]=mapped_column(Integer,primary_key=True); user_id:Mapped[int]=mapped_column(ForeignKey("users.id",ondelete="CASCADE"),index=True,nullable=False); token_hash:Mapped[str]=mapped_column(String(64),nullable=False); expires_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False); revoked_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow,nullable=False); user_agent:Mapped[str|None]=mapped_column(String(512)); user:Mapped[User]=relationship(back_populates="refresh_sessions")
class AuditEvent(Base):
 __tablename__="audit_events"
 id:Mapped[int]=mapped_column(Integer,primary_key=True); user_id:Mapped[int|None]=mapped_column(ForeignKey("users.id",ondelete="SET NULL"),index=True); event_type:Mapped[str]=mapped_column(String(80),index=True,nullable=False); created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=utcnow,nullable=False); details:Mapped[str|None]=mapped_column(Text)
