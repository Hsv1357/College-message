import logging
from functools import wraps
from flask import session, redirect, url_for, flash, current_app
from app.firebase_client import (
    get_db,
    normalize_user_id,
    get_internal_auth_email,
    verify_password_with_firebase,
    is_firebase_initialized,
)

logger = logging.getLogger(__name__)

ALLOWED_ROLES = ["admin", "staff", "student", "parent"]


def authenticate_user(user_id: str, password: str, api_key: str):
    """
    Authenticates a user via User ID and Password:
    1. Normalizes user_id.
    2. Queries user_id_mappings in Firestore.
    3. Verifies credentials against Firebase Authentication.
    4. Retrieves profile from Firestore 'users' collection.
    5. Validates role and 'account_status == active'.

    Returns:
        tuple: (success: bool, message: str, user_profile: dict or None)
    """
    if not user_id or not password:
        return False, "User ID and password are required.", None

    norm_id = normalize_user_id(user_id)

    try:
        db = get_db()
        mapping_ref = db.collection("user_id_mappings").document(norm_id).get()

        if not mapping_ref.exists:
            logger.warning("Authentication failed: User ID '%s' not found in mappings.", norm_id)
            # Uniform error message to prevent user enumeration
            return False, "Login failed. Please check your credentials or contact the administrator.", None

        mapping_data = mapping_ref.to_dict() or {}
        auth_email = mapping_data.get("auth_email") or get_internal_auth_email(norm_id)
        expected_uid = mapping_data.get("uid")

        # Authenticate with Firebase Authentication REST API
        auth_result = verify_password_with_firebase(auth_email, password, api_key)
        if not auth_result.get("success"):
            error_code = auth_result.get("error")
            if error_code == "NETWORK_TIMEOUT":
                return False, "Authentication service timeout. Please try again.", None
            return False, "Login failed. Please check your credentials or contact the administrator.", None

        auth_uid = auth_result.get("uid")
        if expected_uid and auth_uid != expected_uid:
            logger.error("UID mismatch for user '%s': expected %s, got %s", norm_id, expected_uid, auth_uid)
            return False, "Authentication error. Account identifier mismatch.", None

        # Fetch user profile from Firestore
        user_doc_ref = db.collection("users").document(auth_uid).get()
        if not user_doc_ref.exists:
            logger.error("User document missing in Firestore for UID '%s'", auth_uid)
            return False, "Login failed. User profile could not be found. Please contact the administrator.", None

        user_profile = user_doc_ref.to_dict() or {}

        # Check account status
        if user_profile.get("account_status") != "active":
            logger.warning("Login attempted for deactivated account '%s'", norm_id)
            return False, "Your account has been deactivated. Please contact the administrator.", None

        # Verify authorized role
        role = user_profile.get("role")
        if role not in ALLOWED_ROLES:
            logger.warning("User '%s' has unauthorized role '%s'", norm_id, role)
            return False, "Unauthorized role assigned to account. Contact administrator.", None

        # Success
        user_profile["uid"] = auth_uid
        return True, "Login successful.", user_profile

    except RuntimeError as re:
        logger.error("Firebase runtime error during login: %s", str(re))
        return False, "Firebase backend is not configured. Please contact the administrator.", None
    except Exception as e:
        logger.error("Unexpected error during login for '%s': %s", norm_id, str(e), exc_info=True)
        return False, "A system error occurred during login. Please try again later.", None


def login_required(f):
    """Decorator ensuring that user is logged into the session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """
    Decorator enforcing that the logged-in user possesses one of the specified roles.
    Bypasses frontend-only checks and strictly verifies session server-side.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = session.get("user")
            if not user:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for("auth.login"))

            user_role = user.get("role")
            if user_role not in roles:
                flash("Unauthorized access. You do not have permission to view that resource.", "danger")
                if user_role == "admin":
                    return redirect(url_for("admin.dashboard"))
                else:
                    return redirect(url_for("users.dashboard"))

            return f(*args, **kwargs)
        return decorated_function
    return decorator
