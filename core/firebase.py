import firebase_admin
from firebase_admin import credentials
from .config import settings
import json
import logging

logger = logging.getLogger(__name__)

def init_firebase():
    if not firebase_admin._apps:
        try:
            if settings.FIREBASE_SERVICE_ACCOUNT_JSON and settings.FIREBASE_SERVICE_ACCOUNT_JSON != "{}":
                cert = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
                cred = credentials.Certificate(cert)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin initialized successfully.")
            else:
                logger.warning("FIREBASE_SERVICE_ACCOUNT_JSON is empty or default. Mocking Firebase init.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin: {e}")
