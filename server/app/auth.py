from jose import JWTError, jwt  
from fastapi import Depends, status, HTTPException
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[int] = None 

from fastapi.security import OAuth2PasswordBearer
import os 
from dotenv import load_dotenv


oauth2_scheme = OAuth2PasswordBearer(tokenUrl = 'login')
load_dotenv()
SECRET_KEY = os.getenv("SECRET-KEY", "2cm6vr9sgzn6d")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes = int(ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm = ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str, credentials_exception):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])
        id: str = payload.get("user_id")

        if id is None:
            raise credentials_exception
        
        token_data = TokenData(id = id)

    except JWTError:
        raise credentials_exception
    
    return token_data 


def get_current_user(token: str = Depends(oauth2_scheme)):
    credential_exception = HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Could not validate credentials")

    token_data = verify_access_token(token, credential_exception)
    return token_data