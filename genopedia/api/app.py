from contextlib import asynccontextmanager
from authlib.integrations.starlette_client import OAuth
from fastapi import Depends,FastAPI,HTTPException,Request,Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy import select,text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from slowapi import Limiter,_rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.sessions import SessionMiddleware
from . import models
from .config import *
from .database import get_db
from .models import User,RefreshSession,AuditEvent,utcnow
from .schemas import Signup,Login,UserOut,AuthOut,Message
from .security import hash_password,verify_password,access_token,decode_access,refresh_token,token_hash,refresh_expiry
limiter=Limiter(key_func=get_remote_address);oauth=OAuth()
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:oauth.register(name="google",client_id=GOOGLE_CLIENT_ID,client_secret=GOOGLE_CLIENT_SECRET,server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",client_kwargs={"scope":"openid email profile"})
if GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET:oauth.register(name="github",client_id=GITHUB_CLIENT_ID,client_secret=GITHUB_CLIENT_SECRET,access_token_url="https://github.com/login/oauth/access_token",authorize_url="https://github.com/login/oauth/authorize",api_base_url="https://api.github.com/",client_kwargs={"scope":"read:user user:email"})
@asynccontextmanager
async def lifespan(app):
 if APP_ENV=="production" and DATABASE_URL.startswith("sqlite"):raise RuntimeError("Production requires a persistent database URL")
 yield
app=FastAPI(title="Genopedia API",version="1.0.0",description="Genopedia accounts and sessions",lifespan=lifespan)
app.state.limiter=limiter;app.add_exception_handler(RateLimitExceeded,_rate_limit_exceeded_handler);app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SessionMiddleware,secret_key=SESSION_SECRET_KEY,same_site=COOKIE_SAMESITE,https_only=COOKIE_SECURE,max_age=600)
app.add_middleware(CORSMiddleware,allow_origins=CORS_ORIGINS,allow_credentials=True,allow_methods=["GET","POST","OPTIONS"],allow_headers=["Authorization","Content-Type"])
def set_cookie(response,token):response.set_cookie("genopedia_refresh",token,max_age=REFRESH_TOKEN_DAYS*86400,httponly=True,secure=COOKIE_SECURE,samesite=COOKIE_SAMESITE,path="/auth")
def audit(db,user_id,event):db.add(AuditEvent(user_id=user_id,event_type=event));db.commit()
def issue(db,user,request):
 token=refresh_token();db.add(RefreshSession(user_id=user.id,token_hash=token_hash(token),expires_at=refresh_expiry(),user_agent=request.headers.get("user-agent","")[:512] or None));db.commit()
 return access_token(user.id),token
def response_for(user,token):return AuthOut(access_token=token,expires_in=ACCESS_TOKEN_MINUTES*60,user=UserOut.model_validate(user))
@app.get("/health/live",tags=["health"])
def live():return {"status":"ok"}
@app.get("/health/ready",tags=["health"])
def ready(db:Session=Depends(get_db)):db.execute(text("SELECT 1"));return {"status":"ready"}
@app.post("/auth/signup",response_model=AuthOut,status_code=201,tags=["auth"])
@limiter.limit("5/minute")
def signup(request:Request,payload:Signup,response:Response,db:Session=Depends(get_db)):
 email=str(payload.email).lower().strip()
 if db.scalar(select(User.id).where(User.email==email)) is not None:raise HTTPException(409,"An account with this email already exists")
 user=User(email=email,full_name=payload.full_name,password_hash=hash_password(payload.password),email_verified=False);db.add(user)
 try:db.commit();db.refresh(user)
 except IntegrityError:db.rollback();raise HTTPException(409,"An account with this email already exists") from None
 access,refresh=issue(db,user,request);set_cookie(response,refresh);audit(db,user.id,"account.signup");return response_for(user,access)
@app.post("/auth/login",response_model=AuthOut,tags=["auth"])
@limiter.limit("8/minute")
def login(request:Request,payload:Login,response:Response,db:Session=Depends(get_db)):
 user=db.scalar(select(User).where(User.email==str(payload.email).lower().strip()))
 if user is None or not verify_password(payload.password,user.password_hash):audit(db,user.id if user else None,"auth.login_failed");raise HTTPException(401,"Invalid email or password")
 if not user.is_active:raise HTTPException(403,"Account is disabled")
 access,refresh=issue(db,user,request);set_cookie(response,refresh);audit(db,user.id,"auth.login");return response_for(user,access)
@app.post("/auth/refresh",response_model=AuthOut,tags=["auth"])
@limiter.limit("20/minute")
def refresh(request:Request,response:Response,db:Session=Depends(get_db)):
 raw=request.cookies.get("genopedia_refresh")
 if not raw:raise HTTPException(401,"Refresh session required")
 session=db.scalar(select(RefreshSession).where(RefreshSession.token_hash==token_hash(raw)));now=utcnow()
 expiry=session.expires_at if session else now
 if expiry.tzinfo is None:expiry=expiry.replace(tzinfo=now.tzinfo)
 if session is None or session.revoked_at is not None or expiry<=now or not session.user.is_active:
  response.delete_cookie("genopedia_refresh",path="/auth",secure=COOKIE_SECURE,httponly=True,samesite=COOKIE_SAMESITE);raise HTTPException(401,"Refresh session expired or revoked")
 user=session.user;session.revoked_at=now;new=refresh_token();db.add(RefreshSession(user_id=user.id,token_hash=token_hash(new),expires_at=refresh_expiry(),user_agent=request.headers.get("user-agent","")[:512] or None));db.commit();set_cookie(response,new);return response_for(user,access_token(user.id))
@app.post("/auth/logout",response_model=Message,tags=["auth"])
def logout(request:Request,response:Response,db:Session=Depends(get_db)):
 raw=request.cookies.get("genopedia_refresh")
 if raw:
  session=db.scalar(select(RefreshSession).where(RefreshSession.token_hash==token_hash(raw)))
  if session and session.revoked_at is None:session.revoked_at=utcnow();db.commit()
 response.delete_cookie("genopedia_refresh",path="/auth",secure=COOKIE_SECURE,httponly=True,samesite=COOKIE_SAMESITE);return Message(message="Signed out")
@app.get("/auth/me",response_model=UserOut,tags=["auth"])
def me(credentials:HTTPAuthorizationCredentials|None=Depends(HTTPBearer(auto_error=False)),db:Session=Depends(get_db)):
 if not credentials:raise HTTPException(401,"Authentication required")
 uid=decode_access(credentials.credentials);user=db.get(User,uid) if uid else None
 if not user or not user.is_active:raise HTTPException(401,"Invalid or expired access token")
 return UserOut.model_validate(user)
@app.get("/auth/oauth/{provider}/login",tags=["oauth"])
async def oauth_login(provider:str,request:Request):
 client=getattr(oauth,provider,None) if provider in {"google","github"} else None
 if client is None:raise HTTPException(404,"OAuth provider is not configured")
 return await client.authorize_redirect(request,f"{API_PUBLIC_URL}/auth/oauth/{provider}/callback")
@app.get("/auth/oauth/{provider}/callback",tags=["oauth"])
async def oauth_callback(provider:str,request:Request,db:Session=Depends(get_db)):
 client=getattr(oauth,provider,None) if provider in {"google","github"} else None
 if client is None:raise HTTPException(404,"OAuth provider is not configured")
 token=await client.authorize_access_token(request)
 if provider=="google":
  profile=token.get("userinfo") or await client.userinfo(token=token);email=str(profile.get("email","")).lower().strip();verified=bool(profile.get("email_verified"));name=profile.get("name")
 else:
  profile=(await client.get("user",token=token)).json();emails=(await client.get("user/emails",token=token)).json();verified_email=next((e.get("email") for e in emails if e.get("primary") and e.get("verified")),None);email=str(verified_email or "").lower().strip();verified=bool(verified_email);name=profile.get("name") or profile.get("login")
 if not email or not verified:raise HTTPException(400,"Provider did not supply a verified email")
 user=db.scalar(select(User).where(User.email==email))
 if user is None:
  user=User(email=email,full_name=str(name)[:120] if name else None,email_verified=True);db.add(user)
  try:db.commit();db.refresh(user)
  except IntegrityError:db.rollback();user=db.scalar(select(User).where(User.email==email))
 elif not user.email_verified:user.email_verified=True;db.commit()
 if user is None or not user.is_active:raise HTTPException(403,"Account is disabled")
 access,refresh=issue(db,user,request);audit(db,user.id,"auth.oauth."+provider);redirect=RedirectResponse(f"{FRONTEND_URL}/auth/callback#access_token={access}",status_code=302);set_cookie(redirect,refresh);return redirect
