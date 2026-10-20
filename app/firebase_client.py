import os
import logging
import requests
import firebase_admin
from firebase_admin import credentials, firestore, auth

logger = logging.getLogger(__name__)

# Global state trackers
_app_initialized = False
_initialization_error = None
_db_client = None


def normalize_user_id(user_id: str) -> str:
    """
    Normalizes a User ID consistently across the system.
    Converts to lowercase and strips leading/trailing whitespace.
    Example: 'Admin-2004' -> 'admin-2004'
    """
    if not user_id:
        return ""
    return str(user_id).strip().lower()


def get_internal_auth_email(user_id: str) -> str:
    """
    Generates a deterministic, collision-safe internal authentication email
    for Firebase Authentication from an application User ID.
    Example: 'Admin-2004' -> 'admin-2004@auth.campusconnect.internal'
    """
    norm_id = normalize_user_id(user_id)
    return f"{norm_id}@auth.campusconnect.internal"


def init_firebase(config=None):
    """
    Initializes the Firebase Admin SDK using the configured credentials.
    Supports service account JSON specified by GOOGLE_APPLICATION_CREDENTIALS or Config.
    Gracefully tracks initialization status if credentials are missing.
    """
    global _app_initialized, _initialization_error, _db_client

    if _app_initialized and _db_client is not None:
        return True, "Firebase already initialized"

    cred_path = None
    if config:
        cred_path = getattr(config, "GOOGLE_APPLICATION_CREDENTIALS", None)
    if not cred_path:
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service_account.json")

    # If already initialized under default app
    try:
        default_app = firebase_admin.get_app()
        _app_initialized = True
        _db_client = firestore.client()
        return True, "Connected to existing Firebase app"
    except ValueError:
        pass  # App not yet initialized, proceed

    # Check if credentials file exists
    if not os.path.exists(cred_path):
        _app_initialized = False
        _initialization_error = (
            f"Firebase service account file not found at '{cred_path}'. "
            "Please download your service account JSON from Firebase Console, "
            "place it in the project directory, and set GOOGLE_APPLICATION_CREDENTIALS."
        )
        logger.warning(_initialization_error)
        return False, _initialization_error

    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        _db_client = firestore.client()
        _app_initialized = True
        _initialization_error = None
        logger.info("Firebase Admin SDK initialized successfully.")
        return True, "Firebase initialized successfully"
    except Exception as e:
        _app_initialized = False
        _initialization_error = f"Failed to initialize Firebase Admin SDK: {str(e)}"
        logger.error(_initialization_error)
        return False, _initialization_error


def is_firebase_initialized() -> bool:
    """Returns True if the Firebase Admin SDK is successfully connected."""
    global _app_initialized
    return _app_initialized


def get_initialization_status() -> dict:
    """Returns a dictionary with current Firebase status and helpful messages."""
    global _app_initialized, _initialization_error
    return {
        "initialized": _app_initialized,
        "error": _initialization_error
    }


def get_db():
    """
    Returns the Firestore database client.
    Raises RuntimeError if Firebase is not initialized.
    """
    global _db_client
    if not _app_initialized or _db_client is None:
        # Try initializing once more
        init_firebase()
        if not _app_initialized or _db_client is None:
            raise RuntimeError(
                _initialization_error or "Firebase Admin SDK has not been initialized. "
                "Check your GOOGLE_APPLICATION_CREDENTIALS in .env."
            )
    return _db_client


def get_auth_admin():
    """
    Returns the firebase_admin.auth module if initialized.
    Raises RuntimeError if Firebase is not initialized.
    """
    if not _app_initialized:
        init_firebase()
        if not _app_initialized:
            raise RuntimeError(
                _initialization_error or "Firebase Admin SDK has not been initialized."
            )
    return auth


def verify_password_with_firebase(auth_email: str, password: str, api_key: str) -> dict:
    """
    Authenticates a user against Firebase Authentication using the Identity Toolkit REST API.
    Does NOT store or compare passwords in Firestore.
    Returns:
        dict: {"success": True, "uid": uid, "id_token": token} or {"success": False, "error": msg}
    """
    if not api_key:
        return {
            "success": False,
            "error": "Firebase API Key is missing. Check FIREBASE_API_KEY in .env."
        }

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = {
        "email": auth_email,
        "password": password,
        "returnSecureToken": True
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()

        if response.status_code == 200:
            return {
                "success": True,
                "uid": data.get("localId"),
                "id_token": data.get("idToken"),
                "email": data.get("email")
            }
        else:
            error_data = data.get("error", {})
            error_msg = error_data.get("message", "AUTHENTICATION_FAILED")
            logger.warning("Firebase Auth rejected login for email %s: %s", auth_email, error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    except requests.RequestException as e:
        logger.error("Network error while connecting to Firebase Auth: %s", str(e))
        return {
            "success": False,
            "error": "NETWORK_TIMEOUT"
        }
