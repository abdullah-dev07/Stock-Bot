import os
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from firebase_admin import auth
import jwt

from ..config import SECRET_KEY, ALGORITHM, FIREBASE_WEB_API_KEY, IS_PRODUCTION
from ..services.auth_service import (
    create_access_token, create_refresh_token,
    verify_firebase_password, get_current_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup")
async def signup(request: Request):
    form = await request.form()
    email = form.get('email')
    password = form.get('password')
    try:
        user = auth.create_user(email=email, password=password)
        print(f"[AUTH] User created: {user.uid}")
        return JSONResponse(
            content={"message": "Signup successful"},
            status_code=status.HTTP_201_CREATED,
        )
    except auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=400, detail="This email address is already in use.")
    except Exception as e:
        print(f"[AUTH] Error creating user: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if not FIREBASE_WEB_API_KEY:
        raise HTTPException(status_code=500, detail="Firebase Web API Key is not configured.")

    email = form_data.username
    password = form_data.password

    try:
        if not verify_firebase_password(email, password):
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(data={"sub": email})
        refresh_token = create_refresh_token(data={"sub": email})

        json_response = JSONResponse(content={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        })
        json_response.set_cookie(
            key="stockbot_token",
            value=access_token,
            httponly=True,
            samesite="none" if IS_PRODUCTION else "lax",
            secure=IS_PRODUCTION,
        )
        return json_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


@router.post("/refresh")
async def refresh(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request body")

    refresh_token = body.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token required")

    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")

        auth.get_user_by_email(email)

        new_access = create_access_token(data={"sub": email})
        new_refresh = create_refresh_token(data={"sub": email})
        return JSONResponse(content={
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
        })
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    except auth.UserNotFoundError:
        raise HTTPException(status_code=401, detail="User not found")


@router.post("/logout")
async def logout():
    response = JSONResponse(content={"message": "Logout successful"})
    response.delete_cookie(key="stockbot_token")
    return response


@router.get("/users/me")
async def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user
