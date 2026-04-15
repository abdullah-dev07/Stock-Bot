from fastapi import Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth
import jwt
import requests
from datetime import datetime, timedelta, timezone

from ..config import (
    SECRET_KEY, ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS,
    FIREBASE_AUTH_URL,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    """FastAPI dependency — validates JWT and returns user dict."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_from_cookie = request.cookies.get("stockbot_token")
    token_to_verify = token_from_cookie or token

    if token_to_verify is None:
        raise credentials_exception

    try:
        payload = jwt.decode(token_to_verify, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") == "refresh":
            raise credentials_exception
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        user = auth.get_user_by_email(email)
        return {"email": user.email, "uid": user.uid}
    except jwt.PyJWTError:
        raise credentials_exception
    except auth.UserNotFoundError:
        raise credentials_exception


def verify_firebase_password(email: str, password: str) -> bool:
    """Verify credentials via Firebase Identity Toolkit REST API."""
    payload = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(FIREBASE_AUTH_URL, json=payload)
    return response.ok
