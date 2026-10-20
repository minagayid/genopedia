"""Email/password authentication API."""
import time
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.security import AuthContext, clear_session_cookies, get_auth_context, hash_password, issue_session, require_csrf, verify_password
from app.db.session import get_db
from app.models.user import AuthSession, User
from app.schemas.auth import LoginInput, SignupInput, UserRead

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupInput, response: Response, db: Session = Depends(get_db)) -> User:
    email = str(payload.email).lower()
    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(email=email, display_name=payload.display_name, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists") from exc
    db.refresh(user)
    db.execute(delete(AuthSession).where(AuthSession.expires_at <= int(time.time())))
    db.commit()
    issue_session(db, user, response, get_settings())
    return user

@router.post("/login", response_model=UserRead)
def login(payload: LoginInput, response: Response, db: Session = Depends(get_db)) -> User:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user is None or not verify_password(payload.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    db.execute(delete(AuthSession).where(AuthSession.expires_at <= int(time.time())))
    db.commit()
    issue_session(db, user, response, get_settings())
    return user

@router.get("/me", response_model=UserRead)
def get_current_account(context: AuthContext = Depends(get_auth_context)) -> User:
    return context.user

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)])
def logout(response: Response, context: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> Response:
    db.delete(context.session)
    db.commit()
    clear_session_cookies(response, get_settings())
    response.status_code = 204
    return response
