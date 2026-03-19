"""
Firebase Authentication helper.
Uses Firebase REST API for sign-in.
"""
import os
import requests
import streamlit as st
import logging

logger = logging.getLogger(__name__)

FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY")
FIREBASE_SIGN_IN_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"

def login(email, password):
    """Authenticate user with Firebase email/password."""
    if not FIREBASE_API_KEY:
        st.error("Firebase API key not configured. Please set FIREBASE_API_KEY.")
        return False
    try:
        payload = {"email": email, "password": password, "returnSecureToken": True}
        r = requests.post(FIREBASE_SIGN_IN_URL, json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        st.session_state["user"] = {
            "email": data["email"],
            "uid": data["localId"],
            "id_token": data["idToken"]
        }
        logger.info(f"User {email} logged in successfully.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Login failed: {e}")
        return False

def logout():
    st.session_state.clear()

def is_authenticated():
    return "user" in st.session_state

def get_user_university_id():
    """Return the user's UID (used as university_id for multi‑tenancy)."""
    return st.session_state["user"]["uid"]