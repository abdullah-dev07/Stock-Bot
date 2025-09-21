


import firebase_admin
from firebase_admin import credentials, firestore
import os








try:
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(base_dir, "firebase-key.json")
    
    cred = credentials.Certificate(key_path)
    
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        print("[FIREBASE] Initialization successful.")
    else:
        print("[FIREBASE] Already initialized.")

except FileNotFoundError:
    print("[FIREBASE] ERROR: 'firebase-key.json' not found. Please ensure the key file is in the 'backend' directory.")
except Exception as e:
    print(f"[FIREBASE] ERROR: Could not initialize Firebase Admin SDK. Error: {e}")


if firebase_admin._apps:
    db = firestore.client()
else:
    db = None
    print("[FIREBASE] Firestore client not available due to initialization failure.")
