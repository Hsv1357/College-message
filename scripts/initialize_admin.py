#!/usr/bin/env python3
"""
CampusConnect - Default Administrator Initialization Script

Provisions the initial administrator account in Firebase Authentication and Cloud Firestore:
- User ID: Admin-2004
- Initial Password: admin@Test123
- Role: admin

Run this script from the project root:
    python scripts/initialize_admin.py
"""

import sys
import os

# Ensure the project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from app.firebase_client import (
    init_firebase,
    is_firebase_initialized,
    get_initialization_status,
    get_db,
    get_auth_admin,
    normalize_user_id,
    get_internal_auth_email,
)
from google.cloud import firestore

ADMIN_USER_ID = "Admin-2004"
ADMIN_INITIAL_PASSWORD = "admin@Test123"
ADMIN_ROLE = "admin"
ADMIN_DISPLAY_NAME = "System Administrator"


def provision_admin():
    print("=" * 60)
    print(" CampusConnect — Administrator Account Provisioning")
    print("=" * 60)

    # 1. Initialize Firebase Admin SDK
    initialized, init_msg = init_firebase()
    if not initialized:
        status = get_initialization_status()
        print("\n[ERROR] Firebase Admin SDK is not initialized!")
        print(f"Details: {status.get('error')}\n")
        print("Setup steps to resolve:")
        print("  1. Download your Firebase service account private key JSON from:")
        print("     Firebase Console -> Project Settings -> Service accounts -> 'Generate new private key'")
        print("  2. Save the file as 'service_account.json' in this project root directory.")
        print("  3. Ensure GOOGLE_APPLICATION_CREDENTIALS=service_account.json in .env")
        print("  4. Re-run: python scripts/initialize_admin.py\n")
        sys.exit(1)

    db = get_db()
    auth_admin = get_auth_admin()

    norm_id = normalize_user_id(ADMIN_USER_ID)
    auth_email = get_internal_auth_email(ADMIN_USER_ID)

    print(f"\nTarget User ID : {ADMIN_USER_ID} (normalized: {norm_id})")
    print(f"Auth Email     : {auth_email}")
    print(f"Assigned Role  : {ADMIN_ROLE}")

    # 2. Check if mapping already exists in Firestore
    mapping_ref = db.collection("user_id_mappings").document(norm_id).get()

    if mapping_ref.exists:
        mapping_data = mapping_ref.to_dict()
        uid = mapping_data.get("uid")
        print(f"\n[INFO] Administrator account '{ADMIN_USER_ID}' already exists.")
        print(f"       Associated UID: {uid}")

        # Check corresponding user profile
        user_ref = db.collection("users").document(uid).get()
        if user_ref.exists:
            user_data = user_ref.to_dict()
            status = user_data.get("account_status", "unknown")
            print(f"       Account Status: {status}")
            print(f"       Role          : {user_data.get('role')}")
        else:
            print("       [WARN] Firestore profile document missing for UID. Re-creating profile...")
            db.collection("users").document(uid).set({
                "uid": uid,
                "user_id": ADMIN_USER_ID,
                "full_name": ADMIN_DISPLAY_NAME,
                "role": ADMIN_ROLE,
                "email": "admin@campusconnect.local",
                "account_status": "active",
                "created_at": firestore.SERVER_TIMESTAMP,
                "created_by": "system_init",
                "updated_at": firestore.SERVER_TIMESTAMP
            })
            print("       Profile restored.")

        print("\n[SUCCESS] No destructive changes made. Existing administrator preserved.")
        return

    # 3. Create Firebase Authentication User
    print("\nCreating Firebase Authentication account...")
    try:
        # Check if auth user already exists by email
        try:
            existing_auth_user = auth_admin.get_user_by_email(auth_email)
            uid = existing_auth_user.uid
            print(f"Found existing Firebase Auth record with UID: {uid}")
        except Exception:
            created_user = auth_admin.create_user(
                email=auth_email,
                password=ADMIN_INITIAL_PASSWORD,
                display_name=ADMIN_DISPLAY_NAME,
                disabled=False
            )
            uid = created_user.uid
            print(f"Created new Firebase Auth record with UID: {uid}")

        # Set custom claims for role-based security in Firebase
        auth_admin.set_custom_user_claims(uid, {"role": ADMIN_ROLE})

    except Exception as e:
        print(f"\n[ERROR] Failed to provision Firebase Authentication user: {str(e)}")
        sys.exit(1)

    # 4. Create Firestore records
    print("Writing Firestore profile and mapping documents...")
    try:
        user_data = {
            "uid": uid,
            "user_id": ADMIN_USER_ID,
            "full_name": ADMIN_DISPLAY_NAME,
            "role": ADMIN_ROLE,
            "email": "admin@campusconnect.local",
            "account_status": "active",
            "created_at": firestore.SERVER_TIMESTAMP,
            "created_by": "system_init",
            "updated_at": firestore.SERVER_TIMESTAMP
        }

        mapping_data = {
            "user_id": ADMIN_USER_ID,
            "normalized_user_id": norm_id,
            "uid": uid,
            "auth_email": auth_email,
            "role": ADMIN_ROLE,
            "created_at": firestore.SERVER_TIMESTAMP,
            "created_by": "system_init"
        }

        batch = db.batch()
        batch.set(db.collection("users").document(uid), user_data)
        batch.set(db.collection("user_id_mappings").document(norm_id), mapping_data)
        batch.commit()

        print("\n" + "=" * 60)
        print(" [SUCCESS] Administrator Account Provisioned Successfully!")
        print("=" * 60)
        print(f" User ID       : {ADMIN_USER_ID}")
        print(f" Initial Pass  : {ADMIN_INITIAL_PASSWORD}")
        print(f" Role          : {ADMIN_ROLE}")
        print(f" UID           : {uid}")
        print("=" * 60)
        print("\nRecommended Next Step:")
        print(" - Log in to CampusConnect web portal at http://127.0.0.1:5000/login")
        print(" - Change the administrator password via Firebase Console or Admin SDK procedure.\n")

    except Exception as e:
        print(f"\n[ERROR] Failed to save administrator profile to Firestore: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    provision_admin()
