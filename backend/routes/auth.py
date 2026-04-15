from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from firebase_admin import auth
import jwt

from ..config import IS_PRODUCTION
from ..services.auth_service import get_current_user
from .handlers.auth_handler import AuthHandler

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup")
async def signup(request: Request):
    form = await request.form()
    email = form.get('email')
    password = form.get('password')
    try:
        AuthHandler.signup(email, password)
        return JSONResponse(
            content={"message": "Signup successful"},
            status_code=status.HTTP_201_CREATED,
        )
    except auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=400, detail="This email address is already in use.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[AUTH] Error creating user: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        tokens = AuthHandler.login(form_data.username, form_data.password)
    except EnvironmentError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    json_response = JSONResponse(content=tokens)
    json_response.set_cookie(
        key="stockbot_token",
        value=tokens["access_token"],
        httponly=True,
        samesite="none" if IS_PRODUCTION else "lax",
        secure=IS_PRODUCTION,
    )
    return json_response


@router.post("/refresh")
async def refresh(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid request body")

    try:
        tokens = AuthHandler.refresh_tokens(body.get("refresh_token"))
        return JSONResponse(content=tokens)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (PermissionError, jwt.ExpiredSignatureError):
        raise HTTPException(status_code=401, detail="Refresh token expired or invalid")
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
