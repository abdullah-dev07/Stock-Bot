import firebase_admin
from firebase_admin import credentials, firestore
import os


def _get_firebase_credentials():
    """
    Try to get Firebase credentials from:
    1. Local firebase-key.json file (for local development)
    2. Environment variables (for production/Render deployment)
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    key_path = os.path.join(base_dir, "firebase-key.json")

    if os.path.exists(key_path):
        print("[FIREBASE] Using local firebase-key.json file.")
        return credentials.Certificate(key_path)

    print("[FIREBASE] firebase-key.json not found. Trying environment variables...")

    project_id = os.environ.get("FIREBASE_PROJECT_ID")
    private_key = os.environ.get("FIREBASE_PRIVATE_KEY")
    client_email = os.environ.get("FIREBASE_CLIENT_EMAIL")

    if project_id and private_key and client_email:
        private_key = private_key.replace("\\n", "\n")

        cred_dict = {
            "type": "service_account",
            "project_id": project_id,
            "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID") or "",
            "private_key": private_key,
            "client_email": client_email,
            "client_id": os.environ.get("FIREBASE_CLIENT_ID") or "",
            "auth_uri": os.environ.get("FIREBASE_AUTH_URI") or "https://accounts.google.com/o/oauth2/auth",
            "token_uri": os.environ.get("FIREBASE_TOKEN_URI") or "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": os.environ.get("FIREBASE_AUTH_PROVIDER_X509_CERT_URL") or "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_X509_CERT_URL") or "",
        }
        print("[FIREBASE] Using environment variables for credentials.")
        return credentials.Certificate(cred_dict)

    print("[FIREBASE] ERROR: No Firebase credentials found!")
    return None


try:
    cred = _get_firebase_credentials()
    if cred:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            print("[FIREBASE] Initialization successful.")
        else:
            print("[FIREBASE] Already initialized.")
    else:
        print("[FIREBASE] Skipping initialization - no credentials available.")
except Exception as e:
    print(f"[FIREBASE] ERROR: Could not initialize Firebase Admin SDK. Error: {e}")

db = firestore.client() if firebase_admin._apps else None
if not db:
    print("[FIREBASE] Firestore client not available due to initialization failure.")
