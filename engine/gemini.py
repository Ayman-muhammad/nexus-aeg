"""
Gemini API wrapper for natural‑language explanations and data extraction.
Uses Vertex AI with explicit credentials from the Firebase service account.
"""
import os
import json
import logging
from typing import List, Dict, Optional, Any

import google.cloud.aiplatform as aiplatform
from google.oauth2 import service_account
from vertexai.preview.generative_models import GenerativeModel, ChatSession

logger = logging.getLogger(__name__)

# List of possible Gemini model names (newest first)
GEMINI_MODELS = [
    "gemini-1.5-pro",
    "gemini-1.0-pro",
    "gemini-pro"
]

def _load_service_account_credentials() -> Optional[service_account.Credentials]:
    """Load service account credentials from environment or file (same as Firebase)."""
    cred_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if cred_json:
        try:
            cred_dict = json.loads(cred_json)
            logger.info("Loaded service account from environment variable.")
            return service_account.Credentials.from_service_account_info(cred_dict)
        except Exception as e:
            logger.exception("Failed to parse FIREBASE_SERVICE_ACCOUNT JSON")
            return None

    # Try file-based credentials
    key_path = os.environ.get("FIREBASE_KEY_PATH", "firebase-key.json")
    if os.path.exists(key_path):
        try:
            logger.info(f"Loaded service account from file: {key_path}")
            return service_account.Credentials.from_service_account_file(key_path)
        except Exception as e:
            logger.exception(f"Failed to load credentials from {key_path}")
            return None

    logger.warning("No service account credentials found for Gemini.")
    return None

class GeminiReasoner:
    def __init__(self):
        self.project_id = os.environ.get("GCP_PROJECT")
        self.location = os.environ.get("GCP_LOCATION", "us-central1")
        self.model = None
        self.chat: Optional[ChatSession] = None
        self.model_name_used = None
        self._creds_loaded = False

        # Load credentials (same as Firebase)
        credentials = _load_service_account_credentials()
        if credentials:
            self._creds_loaded = True

        if not self.project_id:
            logger.warning("GCP_PROJECT not set. Gemini disabled.")
            return

        if not credentials:
            logger.warning("Firebase service account credentials missing. Gemini disabled.")
            return

        # Try to initialise Vertex AI and find a working model
        try:
            aiplatform.init(
                project=self.project_id,
                location=self.location,
                credentials=credentials
            )
            logger.info(f"Vertex AI initialised for project {self.project_id}")

            # Try each model until one works
            for model_name in GEMINI_MODELS:
                try:
                    self.model = GenerativeModel(model_name)
                    # Test with a simple prompt
                    test_response = self.model.generate_content("test")
                    if test_response:
                        self.model_name_used = model_name
                        self.chat = self.model.start_chat()
                        logger.info(f"Successfully connected using model: {model_name}")
                        break
                except Exception as e:
                    logger.debug(f"Model {model_name} failed: {e}")
                    continue

            if not self.model:
                logger.error("No working Gemini model found. Check project permissions and enabled APIs.")
            else:
                logger.info(f"GeminiReasoner ready with model: {self.model_name_used}")

        except Exception as e:
            logger.exception("Failed to initialise Vertex AI")
            self.model = None

    def _get_expected_fields(self, file_type: str) -> str:
        """Return the expected JSON schema for a given file type."""
        schemas = {
            'buildings': 'code (string), name (string), capacity (integer)',
            'units': 'code (string), name (string), year (integer), semester (integer), exam_duration_minutes (integer)',
            'assessments': 'unit_code (string), student_count (integer), current_room (string), current_slot (string, format "YYYY-MM-DD HH:MM")'
        }
        return schemas.get(file_type, '')

    def extract_data(self, text: str, file_type: str) -> List[Dict[str, Any]]:
        """
        Use Gemini to extract structured data from unstructured text (PDF/DOCX).
        Returns a list of dictionaries matching the expected schema.
        """
        if not self.model:
            logger.warning("Gemini not available – cannot extract data.")
            return []

        prompt = f"""
You are an AI assistant for a university exam scheduling system.
Extract {file_type} data from the following text.
The expected format is a list of JSON objects with these fields:
{self._get_expected_fields(file_type)}

Only output valid JSON. Do not include any other text, markdown, or explanations.

Text:
{text}
"""
        try:
            response = self.model.generate_content(prompt)
            # Clean response – remove any potential markdown fences
            raw = response.text.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.endswith("```"):
                raw = raw[:-3]
            data = json.loads(raw)
            # Ensure it's a list
            if isinstance(data, dict):
                data = [data]
            logger.info(f"Gemini extracted {len(data)} {file_type} records.")
            return data
        except Exception as e:
            logger.exception("Gemini extraction failed")
            return []

    def explain_choice(self, unit_code: str, option: dict) -> str:
        """
        Generate a human‑readable explanation for why a particular room/slot was chosen.
        """
        if not self.model:
            return (f"Recommended {option['proposed_room']} at {option['proposed_slot']} "
                    f"with score {option.get('score', 0):.2f}. This balances capacity and historical preferences.")

        prompt = (
            f"You are Nexus AEG, an AI exam governance system. "
            f"Explain why moving {unit_code} to room {option['proposed_room']} at {option['proposed_slot']} "
            f"is a good choice. Mention capacity, historical usage, and fairness. "
            f"Keep it concise (max 2 sentences)."
        )
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.exception("Gemini API call failed")
            return "Explanation unavailable due to API error."

    def chat_response(self, user_message: str) -> str:
        """
        For the assistant chat feature.
        """
        if not self.model or not self.chat:
            return "I'm sorry, the AI assistant is currently offline. Please check your configuration:\n" \
                   f"- Project ID: {self.project_id}\n" \
                   f"- Credentials: {'Loaded' if self._creds_loaded else 'Missing'}\n" \
                   f"- Model: {self.model_name_used or 'None'}"
        try:
            response = self.chat.send_message(user_message)
            return response.text.strip()
        except Exception as e:
            logger.exception("Gemini chat failed")
            return f"I encountered an error: {str(e)}. Please try again."