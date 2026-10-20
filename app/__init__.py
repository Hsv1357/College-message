import os
import logging
from flask import Flask, render_template, session, redirect, url_for
from flask_wtf.csrf import CSRFProtect, CSRFError
from app.config import config_by_name
from app.firebase_client import init_firebase, is_firebase_initialized

csrf = CSRFProtect()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
)
logger = logging.getLogger(__name__)


def create_app(config_name=None):
    """
    Application factory for CampusConnect.
    Configures Flask, CSRF protection, Firebase Admin SDK, blueprints, and error handlers.
    """
    if not config_name:
        config_name = os.getenv("FLASK_ENV", "development").lower()

    app = Flask(__name__)
    config_class = config_by_name.get(config_name, config_by_name["development"])
    app.config.from_object(config_class)

    # Initialize CSRF Protection
    csrf.init_app(app)

    # Initialize Firebase Admin SDK
    success, msg = init_firebase(config_class)
    if success:
        logger.info("Firebase initialization: %s", msg)
    else:
        logger.warning("Firebase initialization pending: %s", msg)

    # Context processors for templates
    @app.context_processor
    def inject_global_template_vars():
        return {
            "app_name": "CampusConnect",
            "current_user": session.get("user"),
            "is_firebase_connected": is_firebase_initialized()
        }

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.users.routes import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(users_bp)

    # Error handlers
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        logger.warning("CSRF validation failed: %s", str(e.description))
        return render_template(
            "login.html",
            csrf_error="Your security token has expired. Please try submitting again."
        ), 400

    @app.errorhandler(404)
    def handle_not_found(e):
        return render_template("base.html", error_title="404 - Page Not Found", error_message="The page you requested could not be located."), 404

    @app.errorhandler(403)
    def handle_forbidden(e):
        return render_template("base.html", error_title="403 - Forbidden", error_message="You do not have permission to access this resource."), 403

    @app.errorhandler(500)
    def handle_server_error(e):
        logger.error("Internal Server Error: %s", str(e), exc_info=True)
        return render_template("base.html", error_title="500 - Server Error", error_message="An unexpected system error occurred. Please contact the administrator."), 500

    return app
