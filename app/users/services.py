import logging
from app.firebase_client import get_db

logger = logging.getLogger(__name__)


def get_user_profile_by_uid(uid: str) -> dict:
    """Fetches user profile document by UID from Firestore."""
    try:
        db = get_db()
        doc = db.collection("users").document(uid).get()
        if doc.exists:
            profile = doc.to_dict()
            profile["uid"] = doc.id
            return profile
    except Exception as e:
        logger.error("Failed to load profile for UID %s: %s", uid, str(e))
    return None
