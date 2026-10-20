import hashlib,secrets
from datetime import datetime,timedelta,timezone
import jwt
from pwdlib import PasswordHash
from .config import ACCESS_TOKEN_MINUTES,JWT_SECRET_KEY,REFRESH_TOKEN_DAYS
_hasher=PasswordHash.recommended()
def hash_password(password:str)->str:return _hasher.hash(password)
def verify_password(password:str,encoded:str|None)->bool:
 if not encoded:return False
 try:return _hasher.verify(password,encoded)
 except Exception:return False
def access_token(user_id:int)->str:
 now=datetime.now(timezone.utc);return jwt.encode({"sub":str(user_id),"iat":now,"exp":now+timedelta(minutes=ACCESS_TOKEN_MINUTES),"type":"access"},JWT_SECRET_KEY,algorithm="HS256")
def decode_access(token:str)->int|None:
 try:
  d=jwt.decode(token,JWT_SECRET_KEY,algorithms=["HS256"],options={"require":["sub","iat","exp"]});return int(d["sub"]) if d.get("type")=="access" else None
 except (jwt.PyJWTError,ValueError,TypeError,KeyError):return None
def refresh_token()->str:return secrets.token_urlsafe(48)
def token_hash(token:str)->str:return hashlib.sha256(token.encode()).hexdigest()
def refresh_expiry():return datetime.now(timezone.utc)+timedelta(days=REFRESH_TOKEN_DAYS)
