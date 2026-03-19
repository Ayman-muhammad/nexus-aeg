"""
Notification module.
Sends SMS via Africa's Talking, and in‑app notifications.
"""
import os
import logging
from typing import List, Dict, Optional

try:
    import africastalking
except ImportError:
    africastalking = None

logger = logging.getLogger(__name__)

class Notifier:
    def __init__(self):
        # Initialise Africa's Talking if credentials exist
        self.at_username = os.environ.get("AT_USERNAME")
        self.at_api_key = os.environ.get("AT_API_KEY")
        self.sms_enabled = False
        if self.at_username and self.at_api_key and africastalking:
            try:
                africastalking.initialize(self.at_username, self.at_api_key)
                self.sms_service = africastalking.SMS
                self.sms_enabled = True
                logger.info("Africa's Talking SMS initialised")
            except Exception as e:
                logger.exception("Failed to initialise Africa's Talking")
        else:
            logger.warning("Africa's Talking credentials not set or library missing – SMS disabled")

    def send_sms(self, to: List[str], message: str) -> bool:
        """
        Send an SMS to a list of phone numbers (international format).
        Returns True if successful, False otherwise.
        """
        if not self.sms_enabled:
            logger.info(f"[SMS DISABLED] Would send: {message} to {to}")
            return False
        try:
            response = self.sms_service.send(message, to)
            logger.info(f"SMS sent: {response}")
            return True
        except Exception as e:
            logger.exception("SMS send failed")
            return False

    def notify_students(self, assessment_id: str, subject: str, details: Dict):
        """
        Notify affected students about a change.
        In a real system, you'd fetch student phone numbers from a database.
        For demo, we log and optionally send SMS to a predefined number.
        """
        message = f"Nexus AEG: {subject}. {details}"
        logger.info(f"Notification for assessment {assessment_id}: {message}")

        test_number = os.environ.get("TEST_SMS_NUMBER")
        if test_number:
            self.send_sms([test_number], message)

    def portal_notification(self, user_id: str, message: str):
        """
        Store an in‑app notification (could be in Firestore).
        For now, just log.
        """
        logger.info(f"Portal notification for {user_id}: {message}")

    def send_critical_alert(self, message: str):
        """Send SMS to all configured admin numbers."""
        admin_numbers = os.environ.get("ADMIN_PHONE_NUMBERS", "").split(",")
        if not admin_numbers or not self.sms_enabled:
            logger.info(f"Critical alert (not sent): {message}")
            return
        for number in admin_numbers:
            if number.strip():
                self.send_sms([number.strip()], f"[NEXUS CRITICAL] {message}")