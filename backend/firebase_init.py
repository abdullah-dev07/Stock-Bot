# FILE: backend/firebase_init.py
# PURPOSE: Initializes the connection to Firebase.

import firebase_admin
from firebase_admin import credentials, firestore
import os

# --- Firebase Initialization ---
# IMPORTANT: You need to generate a private key file for your Firebase project.
# 1. Go to your Firebase project settings -> Service accounts.
# 2. Click "Generate new private key" and download the JSON file.
# 3. Rename it to "firebase-key.json" and place it in your "backend" folder.
# 4. Make sure to add "firebase-key.json" to your .gitignore file to keep it private!

try:
    # Get the absolute path to the directory where this script is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    key_path = os.path.join(base_dir, "firebase-key.json")
    
    cred = credentials.Certificate(key_path)
    
    # Check if the app is already initialized to prevent errors on reload
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        print("[FIREBASE] Initialization successful.")
    else:
        print("[FIREBASE] Already initialized.")

except FileNotFoundError:
    print("[FIREBASE] ERROR: 'firebase-key.json' not found. Please ensure the key file is in the 'backend' directory.")
except Exception as e:
    print(f"[FIREBASE] ERROR: Could not initialize Firebase Admin SDK. Error: {e}")

# This check ensures the app doesn't crash if initialization fails
if firebase_admin._apps:
    db = firestore.client()
else:
    db = None
    print("[FIREBASE] Firestore client not available due to initialization failure.")
