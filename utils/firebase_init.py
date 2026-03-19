"""
Firebase initialization utility.

Supports:
- FIREBASE_KEY_PATH (recommended)
- FIREBASE_SERVICE_ACCOUNT (optional JSON string fallback)

Returns:
- Firestore DB client
- Firebase App instance
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase():
    """
    Initialize Firebase safely (Streamlit-safe).

    Returns:
        db (firestore.Client): Firestore database client
        app (firebase_admin.App): Firebase app instance
    """

    # ✅ Prevent re-initialization (important for Streamlit reloads)
    if firebase_admin._apps:
        app = firebase_admin.get_app()
    else:
        key_path = os.getenv("FIREBASE_KEY_PATH")
        json_env = os.getenv("FIREBASE_SERVICE_ACCOUNT")

        # ✅ Option 1: File path (recommended)
        if key_path:
            if not os.path.exists(key_path):
                raise RuntimeError(
                    f"Firebase key file not found at: {key_path}"
                )
            cred = credentials.Certificate(key_path)

        # ✅ Option 2: Raw JSON string
        elif json_env:
            try:
                cred_dict = json.loads(json_env)
                cred = credentials.Certificate(cred_dict)
            except Exception as e:
                raise RuntimeError(
                    f"FIREBASE_SERVICE_ACCOUNT contains invalid JSON: {e}"
                )

        # ❌ Nothing provided
        else:
            raise RuntimeError(
                "Firebase credentials not found.\n"
                "Set FIREBASE_KEY_PATH or FIREBASE_SERVICE_ACCOUNT."
            )

        # Initialize Firebase app
        app = firebase_admin.initialize_app(cred)

    # ✅ ALWAYS create Firestore client
    db = firestore.client()

    return db, app