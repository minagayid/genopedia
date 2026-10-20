"""Argon2 password hashes and revocable cookie sessions with CSRF protection."""
from dataclasses import dataclass
import hashlib
import hmac
import secrets
import time
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import Response
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.user import AuthSession, User

SESSION_COOKIE = "genopedia_session"
CSRF_COOKIE = "genopedia_csrf"
_password_hasher = PasswordHash.recommended()

def hash_password(password: str) -> str:
    return _password_hasher.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password, password_hash)
    except (ValueError, TypeError):
        return False

def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class AuthContext:
    user: User
    session: AuthSession

def issue_session(db: Session, user: User, response: Response, settings: Settings) -> None:
    raw_token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    now = int(time.time())
    row = AuthSession(user_id=user.id, token_hash=token_digest(raw_token), csrf_token_hash=token_digest(csrf_token), created_at=now, expires_at=now + settings.session_ttl_seconds)
    db.add(row)
    db.commit()
    options = {"max_age": settings.session_ttl_seconds, "httponly": True, "secure": settings.secure_cookies, "samesite": "lax", "path": "/", "domain": settings.cookie_domain}
    response.set_cookie(SESSION_COOKIE, raw_token, **options)
    response.set_cookie(CSRF_COOKIE, csrf_token, httponly=False, **{key: value for key, value in options.items() if key != "httponly"})

def clear_session_cookies(response: Response, settings: Settings) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", domain=settings.cookie_domain, secure=settings.secure_cookies, httponly=True, samesite="lax")
    response.delete_cookie(CSRF_COOKIE, path="/", domain=settings.cookie_domain, secure=settings.secure_cookies, httponly=False, samesite="lax")

def get_auth_context(request: Request, db: Session = Depends(get_db)) -> AuthContext:
    raw_token = request.cookies.get(SESSION_COOKIE)
    if not raw_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    row = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_digest(raw_token), AuthSession.expires_at > int(time.time())))
    if row is None:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    user = db.get(User, row.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Account is unavailable")
    return AuthContext(user=user, session=row)

def require_csrf(request: Request, context: AuthContext = Depends(get_auth_context)) -> None:
    cookie_token = request.cookies.get(CSRF_COOKIE, "")
    header_token = request.headers.get("X-CSRF-Token", "")
    if not cookie_token or not header_token:
        raise HTTPException(status_code=403, detail="CSRF token required")
    if not hmac.compare_digest(cookie_token, header_token):
        raise HTTPException(status_code=403, detail="CSRF token mismatch")
    if not hmac.compare_digest(token_digest(cookie_token), context.session.csrf_token_hash):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
