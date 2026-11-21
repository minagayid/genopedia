from fastapi import Depends,HTTPException
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
from .security import decode_access
_bearer=HTTPBearer(auto_error=False)
def get_current_user(credentials:HTTPAuthorizationCredentials|None=Depends(_bearer),db:Session=Depends(get_db))->User:
 if not credentials:raise HTTPException(401,"Authentication required")
 uid=decode_access(credentials.credentials);user=db.get(User,uid) if uid else None
 if not user or not user.is_active:raise HTTPException(401,"Invalid or expired access token")
 return user
