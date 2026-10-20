"""FastAPI application and runtime health checks."""
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.core.config import get_settings
from app.db.session import get_db

settings = get_settings()
app = FastAPI(title="Genopedia API", version="0.3.0", description="Local-first genomics reporting with account services.", redoc_url=None)
if settings.cors_origins:
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "OPTIONS"], allow_headers=["Content-Type", "X-CSRF-Token"])

@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self';")
    if settings.app_env.lower() == "production" and settings.secure_cookies:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
    return response

app.include_router(auth_router)
app.include_router(users_router)

@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "index.html", media_type="text/html")

@app.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    return {"status": "alive"}

@app.get("/health/ready", tags=["health"])
def readiness(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database is not ready") from exc
    return {"status": "ready", "database": "connected"}
