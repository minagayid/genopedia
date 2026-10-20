"""Authenticated profile endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.security import AuthContext, get_auth_context, require_csrf
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import ProfileUpdate, UserRead

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me", response_model=UserRead)
def read_my_profile(context: AuthContext = Depends(get_auth_context)) -> User:
    return context.user

@router.patch("/me", response_model=UserRead, dependencies=[Depends(require_csrf)])
def update_my_profile(payload: ProfileUpdate, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> User:
    context.user.display_name = payload.display_name
    db.add(context.user)
    db.commit()
    db.refresh(context.user)
    return context.user
