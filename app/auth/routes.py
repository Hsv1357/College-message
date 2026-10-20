from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from app.auth.services import authenticate_user
from app.firebase_client import get_initialization_status

auth_bp = Blueprint("auth", __name__, url_prefix="")


@auth_bp.route("/", methods=["GET"])
def index():
    """Root route redirecting to login or dashboard based on session."""
    user = session.get("user")
    if user:
        if user.get("role") == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("users.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handles user login with User ID and Password."""
    # If already logged in, redirect to appropriate dashboard
    user = session.get("user")
    if user:
        if user.get("role") == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("users.dashboard"))

    # Check Firebase connection status to inform administrator if config is missing
    firebase_status = get_initialization_status()

    if request.method == "POST":
        user_id = request.form.get("user_id", "").strip()
        password = request.form.get("password", "")

        if not user_id or not password:
            flash("Please enter both User ID and Password.", "warning")
            return render_template("login.html", user_id=user_id, firebase_status=firebase_status)

        api_key = current_app.config.get("FIREBASE_API_KEY")

        success, message, user_profile = authenticate_user(user_id, password, api_key)

        if not success:
            flash(message, "danger")
            return render_template("login.html", user_id=user_id, firebase_status=firebase_status)

        # Establish secure server-side session
        session.clear()
        session["user"] = {
            "uid": user_profile.get("uid"),
            "user_id": user_profile.get("user_id"),
            "full_name": user_profile.get("full_name"),
            "role": user_profile.get("role"),
            "email": user_profile.get("email", ""),
            "department": user_profile.get("department", ""),
            "class_name": user_profile.get("class_name", "")
        }
        session.permanent = True

        flash(f"Welcome back, {user_profile.get('full_name')}!", "success")

        if user_profile.get("role") == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("users.dashboard"))

    return render_template("login.html", firebase_status=firebase_status)


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """Clears user session and terminates application access."""
    session.clear()
    flash("You have been logged out safely.", "info")
    return redirect(url_for("auth.login"))
