import os
APP_ENV=os.getenv("APP_ENV","development").lower(); DATABASE_URL=os.getenv("DATABASE_URL","sqlite:///./genopedia.db")
JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY","dev-only-change-this-secret-before-deploying-32chars"); SESSION_SECRET_KEY=os.getenv("SESSION_SECRET_KEY",JWT_SECRET_KEY)
ACCESS_TOKEN_MINUTES=int(os.getenv("ACCESS_TOKEN_MINUTES","15")); REFRESH_TOKEN_DAYS=int(os.getenv("REFRESH_TOKEN_DAYS","30"))
FRONTEND_URL=os.getenv("FRONTEND_URL","http://localhost:3000").rstrip("/"); API_PUBLIC_URL=os.getenv("API_PUBLIC_URL","http://localhost:8000").rstrip("/")
COOKIE_SECURE=os.getenv("COOKIE_SECURE","true" if APP_ENV=="production" else "false").lower() in {"1","true","yes"}; COOKIE_SAMESITE=os.getenv("COOKIE_SAMESITE","lax").lower()
CORS_ORIGINS=[x.strip() for x in os.getenv("CORS_ORIGINS",FRONTEND_URL).split(",") if x.strip()]
GOOGLE_CLIENT_ID=os.getenv("GOOGLE_CLIENT_ID",""); GOOGLE_CLIENT_SECRET=os.getenv("GOOGLE_CLIENT_SECRET",""); GITHUB_CLIENT_ID=os.getenv("GITHUB_CLIENT_ID",""); GITHUB_CLIENT_SECRET=os.getenv("GITHUB_CLIENT_SECRET","")
if APP_ENV=="production" and (len(JWT_SECRET_KEY)<32 or JWT_SECRET_KEY.startswith("dev-only") or len(SESSION_SECRET_KEY)<32 or not COOKIE_SECURE): raise RuntimeError("Production requires strong JWT/SESSION secrets and COOKIE_SECURE=true")
if COOKIE_SAMESITE not in {"lax","strict","none"} or (COOKIE_SAMESITE=="none" and not COOKIE_SECURE): raise RuntimeError("Invalid cookie policy; SameSite=None requires Secure")
