#!/usr/bin/env python3
"""
CampusConnect - College Web Application (Phase 1)
Entry point to run the Flask development server.
"""

import os
from dotenv import load_dotenv

# Load local environment settings
load_dotenv()

from app import create_app
from app.firebase_client import is_firebase_initialized, get_initialization_status

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1")

    print("\n" + "=" * 65)
    print(" CampusConnect — College Web Application (Phase 1)")
    print("=" * 65)
    print(f" * Server running on: http://{host}:{port}")
    print(f" * Login Page URL   : http://{host}:{port}/login")

    fb_status = get_initialization_status()
    if fb_status.get("initialized"):
        print(" * Firebase Status  : CONNECTED (Cloud Firestore & Auth active)")
    else:
        print(" * Firebase Status  : PENDING CREDENTIALS")
        print("   (Place 'service_account.json' in project root to link Firebase)")
    print("=" * 65 + "\n")

    app.run(host=host, port=port, debug=debug)
