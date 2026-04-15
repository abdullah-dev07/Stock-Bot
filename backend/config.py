import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

# Auth
SECRET_KEY = os.environ.get("SECRET_KEY", "a-secure-default-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
FIREBASE_WEB_API_KEY = os.environ.get("FIREBASE_WEB_API_KEY")
FIREBASE_AUTH_URL = (
    f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
    f"?key={FIREBASE_WEB_API_KEY}"
)

# API Keys
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY")
SEC_API_KEY = os.environ.get("SEC_API_KEY")

# External URLs
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

# CORS
CORS_ORIGINS = ["*"]
IS_PRODUCTION = bool(os.environ.get("RENDER"))

# Cache
CACHE_DURATION_MINUTES = 600

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
BUILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../react-frontend/dist"))
