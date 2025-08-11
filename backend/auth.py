# FILE: backend/auth.py
# PURPOSE: Handles user signup and login API endpoints for a React frontend.

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from firebase_admin import auth, exceptions
import requests
import os
import jwt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# --- Load environment variables at the top of this file ---
load_dotenv()

from . import firebase_init

# --- Setup ---
# BEST PRACTICE: Add a prefix and common tags to the router for organization.
# All routes in this file will now start with /auth.
auth_router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# --- JWT Configuration ---
SECRET_KEY = os.environ.get("SECRET_KEY", "a-secure-default-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300

# --- Firebase REST API Configuration ---
FIREBASE_WEB_API_KEY = os.environ.get("FIREBASE_WEB_API_KEY")
REST_API_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"

# --- Dependency Setup ---
# The tokenUrl must now include the /auth prefix.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)):
    """Dependency to verify token and get user data, including UID."""
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
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        
        user = auth.get_user_by_email(email)
        return {"email": user.email, "uid": user.uid}

    except jwt.PyJWTError:
        raise credentials_exception
    except auth.UserNotFoundError:
        raise credentials_exception
    
    
# --- API Routes ---

@auth_router.post("/signup")
async def signup(request: Request):
    """
    API endpoint for creating a new user.
    Frontend should POST to: /auth/signup
    """
    form = await request.form()
    email = form.get('email')
    password = form.get('password')
    try:
        user = auth.create_user(email=email, password=password)
        print(f"[AUTH] User created successfully: {user.uid}")
        return JSONResponse(content={"message": "Signup successful"}, status_code=status.HTTP_201_CREATED)
    except exceptions.EmailAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This email address is already in use.")
    except Exception as e:
        print(f"[AUTH] Error creating user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

@auth_router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    API endpoint for logging in and receiving a JWT.
    Frontend should POST to: /auth/token
    """
    if not FIREBASE_WEB_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Firebase Web API Key is not configured on the server."
        )
        
    email = form_data.username
    password = form_data.password
    
    try:
        payload = {'email': email, 'password': password, 'returnSecureToken': True}
        response = requests.post(REST_API_URL, json=payload)
        
        if response.ok:
            access_token = create_access_token(data={"sub": email})
            json_response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
            json_response.set_cookie(
                key="stockbot_token", 
                value=access_token, 
                httponly=True,
                samesite="lax"
            )
            return json_response
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )

@auth_router.post("/logout")
async def logout():
    """
    API endpoint to clear the authentication cookie.
    Frontend should POST to: /auth/logout
    """
    response = JSONResponse(content={"message": "Logout successful"})
    response.delete_cookie(key="stockbot_token")
    return response

@auth_router.get("/users/me")
async def read_user_email(current_user: dict = Depends(get_current_user)):
    """
    Fetches the email of the current user to display in the welcome message.
    Frontend should GET from: /auth/users/me
    """
    return current_user