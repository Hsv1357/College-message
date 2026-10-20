import logging
from datetime import datetime
from google.cloud import firestore
from app.firebase_client import (
    get_db,
    get_auth_admin,
    normalize_user_id,
    get_internal_auth_email,
    is_firebase_initialized,
)

logger = logging.getLogger(__name__)


def get_dashboard_statistics() -> dict:
    """
    Computes real metrics from Cloud Firestore 'users' collection.
    Returns:
        dict containing student, staff, parent counts and active/disabled counts.
    """
    stats = {
        "total_students": 0,
        "total_staff": 0,
        "total_parents": 0,
        "active_accounts": 0,
        "disabled_accounts": 0,
        "total_accounts": 0,
    }

    try:
        db = get_db()
        users_ref = db.collection("users")
        docs = users_ref.stream()

        for doc in docs:
            data = doc.to_dict()
            role = data.get("role")
            status = data.get("account_status", "active")

            stats["total_accounts"] += 1

            if role == "student":
                stats["total_students"] += 1
            elif role == "staff":
                stats["total_staff"] += 1
            elif role == "parent":
                stats["total_parents"] += 1

            if status == "active":
                stats["active_accounts"] += 1
            elif status == "disabled":
                stats["disabled_accounts"] += 1

    except Exception as e:
        logger.error("Error retrieving dashboard statistics: %s", str(e))

    return stats


def get_users_by_role(role: str, search_query: str = None, department_filter: str = None, status_filter: str = None):
    """
    Retrieves all user profiles matching a given role and optional filters.
    """
    users = []
    try:
        db = get_db()
        query = db.collection("users").where("role", "==", role)
        docs = query.stream()

        sq = search_query.strip().lower() if search_query else None
        dept = department_filter.strip().lower() if department_filter else None
        status = status_filter.strip().lower() if status_filter else None

        for doc in docs:
            u = doc.to_dict()
            u["uid"] = doc.id

            # Apply in-memory search and filter for flexible matching
            if sq:
                uid_str = str(u.get("user_id", "")).lower()
                name_str = str(u.get("full_name", "")).lower()
                if sq not in uid_str and sq not in name_str:
                    continue

            if dept and dept != "all":
                u_dept = str(u.get("department", "")).lower()
                if dept != u_dept:
                    continue

            if status and status != "all":
                u_status = str(u.get("account_status", "active")).lower()
                if status != u_status:
                    continue

            # Format created_at for display if it's a timestamp
            created_at = u.get("created_at")
            if hasattr(created_at, "strftime"):
                u["formatted_created_at"] = created_at.strftime("%Y-%m-%d %H:%M")
            else:
                u["formatted_created_at"] = str(created_at or "N/A")

            users.append(u)

        # Sort users by user_id
        users.sort(key=lambda x: str(x.get("user_id", "")))

    except Exception as e:
        logger.error("Error fetching users for role '%s': %s", role, str(e))

    return users


def create_new_account(
    admin_uid: str,
    role: str,
    user_id: str,
    full_name: str,
    password: str,
    email: str = None,
    phone: str = None,
    department: str = None,
    class_name: str = None,
    parent_student_ids: list = None
):
    """
    Creates a new user account:
    1. Validates inputs.
    2. Checks for duplicate User ID in 'user_id_mappings'.
    3. Provisions Firebase Authentication user using Admin SDK.
    4. Writes 'users' and 'user_id_mappings' Firestore documents.
    5. Compensates/rolls back if partial failure occurs.
    """
    if role not in ["student", "staff", "parent", "admin"]:
        return False, f"Invalid role: '{role}'."

    if not user_id or not user_id.strip():
        return False, "User ID cannot be empty."

    if not full_name or not full_name.strip():
        return False, "Full Name cannot be empty."

    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."

    norm_id = normalize_user_id(user_id)
    clean_user_id = user_id.strip()
    auth_email = get_internal_auth_email(clean_user_id)

    db = get_db()
    auth_admin = get_auth_admin()

    # Step 1: Check if User ID mapping already exists
    try:
        existing_mapping = db.collection("user_id_mappings").document(norm_id).get()
        if existing_mapping.exists:
            return False, f"User ID '{clean_user_id}' is already registered."
    except Exception as e:
        logger.error("Database check failed for User ID '%s': %s", norm_id, str(e))
        return False, "Failed to verify User ID uniqueness against database."

    # Step 2: Create Firebase Auth User
    created_auth_user = None
    try:
        created_auth_user = auth_admin.create_user(
            email=auth_email,
            password=password,
            display_name=full_name.strip(),
            disabled=False
        )
    except Exception as e:
        err_msg = str(e)
        logger.error("Firebase Auth user creation failed for '%s': %s", auth_email, err_msg)
        if "EMAIL_EXISTS" in err_msg or "already exists" in err_msg:
            return False, f"An authentication record for User ID '{clean_user_id}' already exists."
        return False, f"Authentication service error: {err_msg}"

    new_uid = created_auth_user.uid

    # Step 3: Create Firestore profile and mapping
    try:
        user_doc_data = {
            "uid": new_uid,
            "user_id": clean_user_id,
            "full_name": full_name.strip(),
            "role": role,
            "email": (email or "").strip(),
            "phone": (phone or "").strip(),
            "department": (department or "").strip(),
            "class_name": (class_name or "").strip(),
            "parent_student_ids": parent_student_ids or [],
            "account_status": "active",
            "created_at": firestore.SERVER_TIMESTAMP,
            "created_by": admin_uid,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }

        mapping_doc_data = {
            "user_id": clean_user_id,
            "normalized_user_id": norm_id,
            "uid": new_uid,
            "auth_email": auth_email,
            "role": role,
            "created_at": firestore.SERVER_TIMESTAMP,
            "created_by": admin_uid,
        }

        # Write both documents
        batch = db.batch()
        batch.set(db.collection("users").document(new_uid), user_doc_data)
        batch.set(db.collection("user_id_mappings").document(norm_id), mapping_doc_data)
        batch.commit()

        logger.info("Successfully provisioned %s account '%s' (UID: %s)", role, clean_user_id, new_uid)
        return True, f"Successfully created {role.capitalize()} account for '{clean_user_id}'."

    except Exception as e:
        logger.error("Firestore write failed for UID %s. Rolling back Auth account... Error: %s", new_uid, str(e))
        # Roll back Firebase Auth account creation to avoid orphaned auth users
        try:
            auth_admin.delete_user(new_uid)
            logger.info("Rolled back created Auth user %s", new_uid)
        except Exception as rollback_err:
            logger.critical("Failed to rollback Auth user %s: %s", new_uid, str(rollback_err))

        return False, "Failed to save user profile to database. Changes were safely reverted."


def update_user_profile(uid: str, update_fields: dict) -> tuple:
    """
    Updates editable profile fields in Firestore.
    Does NOT allow modifying user_id, role, or uid directly.
    """
    allowed_keys = ["full_name", "email", "phone", "department", "class_name", "parent_student_ids"]
    sanitized = {k: v.strip() if isinstance(v, str) else v for k, v in update_fields.items() if k in allowed_keys}

    if not sanitized:
        return False, "No valid update fields provided."

    try:
        db = get_db()
        auth_admin = get_auth_admin()
        sanitized["updated_at"] = firestore.SERVER_TIMESTAMP

        db.collection("users").document(uid).update(sanitized)

        # If full_name changed, also sync Firebase Auth display name
        if "full_name" in sanitized and sanitized["full_name"]:
            try:
                auth_admin.update_user(uid, display_name=sanitized["full_name"])
            except Exception as auth_err:
                logger.warning("Could not sync display_name with Auth: %s", str(auth_err))

        return True, "Profile updated successfully."
    except Exception as e:
        logger.error("Error updating profile for UID %s: %s", uid, str(e))
        return False, f"Failed to update profile: {str(e)}"


def toggle_user_status(uid: str, new_status: str) -> tuple:
    """
    Activates or deactivates a user account across both Firestore and Firebase Auth.
    If disabled: revokes refresh tokens to terminate existing sessions.
    """
    if new_status not in ["active", "disabled"]:
        return False, f"Invalid status: '{new_status}'."

    try:
        db = get_db()
        auth_admin = get_auth_admin()

        # Update Firestore
        db.collection("users").document(uid).update({
            "account_status": new_status,
            "updated_at": firestore.SERVER_TIMESTAMP
        })

        # Update Firebase Auth account state
        is_disabled = (new_status == "disabled")
        auth_admin.update_user(uid, disabled=is_disabled)

        # If disabling, revoke active refresh tokens
        if is_disabled:
            auth_admin.revoke_refresh_tokens(uid)
            logger.info("Revoked refresh tokens for disabled UID %s", uid)

        action_str = "activated" if new_status == "active" else "deactivated"
        return True, f"Account has been successfully {action_str}."

    except Exception as e:
        logger.error("Error toggling account status for UID %s: %s", uid, str(e))
        return False, f"Failed to update account status: {str(e)}"
