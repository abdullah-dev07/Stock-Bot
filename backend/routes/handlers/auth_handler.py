from firebase_admin import auth
import jwt

from ...config import SECRET_KEY, ALGORITHM, FIREBASE_WEB_API_KEY
from ...services.auth_service import (
    create_access_token,
    create_refresh_token,
    verify_firebase_password,
)


class AuthHandler:

    @staticmethod
    def signup(email: str, password: str) -> dict:
        """Create a new user via Firebase Admin SDK."""
        if not email or not password:
            raise ValueError("Email and password are required.")
        user = auth.create_user(email=email, password=password)
        return {"uid": user.uid, "email": email}

    @staticmethod
    def login(email: str, password: str) -> dict:
        """Verify credentials and return a fresh token pair."""
        if not FIREBASE_WEB_API_KEY:
            raise EnvironmentError("Firebase Web API Key is not configured.")
        if not verify_firebase_password(email, password):
            raise PermissionError("Incorrect email or password.")
        access_token = create_access_token(data={"sub": email})
        refresh_token = create_refresh_token(data={"sub": email})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    def refresh_tokens(refresh_token: str) -> dict:
        """Validate a refresh token and issue a new token pair."""
        if not refresh_token:
            raise ValueError("Refresh token is required.")
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise PermissionError("Invalid token type.")
        email = payload.get("sub")
        if not email:
            raise PermissionError("Invalid token payload.")
        auth.get_user_by_email(email)
        new_access = create_access_token(data={"sub": email})
        new_refresh = create_refresh_token(data={"sub": email})
        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
        }
