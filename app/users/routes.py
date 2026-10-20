from flask import Blueprint, render_template, session, redirect, url_for
from app.auth.services import login_required
from app.users.services import get_user_profile_by_uid

users_bp = Blueprint("users", __name__, url_prefix="/role")


@users_bp.route("/dashboard")
@login_required
def dashboard():
    """Role-appropriate landing dashboard for students, staff, and parents."""
    user = session.get("user", {})
    role = user.get("role")

    if role == "admin":
        return redirect(url_for("admin.dashboard"))

    # Attempt to fetch freshest profile from Firestore if available
    profile = get_user_profile_by_uid(user.get("uid")) or user

    return render_template("role_dashboard.html", user=profile, role=role)
