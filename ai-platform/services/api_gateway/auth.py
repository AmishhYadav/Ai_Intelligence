import os
import time
import jwt
from typing import Optional
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

security = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET_KEY", "your_super_secret_jwt_key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

class UserContext(BaseModel):
    user_id: str
    roles: list[str]

def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)) -> UserContext:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        roles = payload.get("roles", [])
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token structure")
            
        # Verify expiration if not done implicitly by PyJWT
        exp = payload.get("exp")
        if exp and exp < time.time():
            raise HTTPException(status_code=401, detail="Token expired")
            
        return UserContext(user_id=user_id, roles=roles)
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid authentication credentials: {e}")
