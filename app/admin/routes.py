from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.auth.services import login_required, role_required
from app.admin.services import (
    get_dashboard_statistics,
    get_users_by_role,
    create_new_account,
    update_user_profile,
    toggle_user_status,
)
from app.firebase_client import get_initialization_status

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    """Admin Dashboard showing real metrics computed from Firestore."""
    stats = get_dashboard_statistics()
    firebase_status = get_initialization_status()
    current_admin = session.get("user")
    return render_template(
        "admin_dashboard.html",
        stats=stats,
        firebase_status=firebase_status,
        current_admin=current_admin
    )


@admin_bp.route("/students")
@login_required
@role_required("admin")
def manage_students():
    """Student management page with search, filter, and account status toggle."""
    q = request.args.get("q", "")
    department = request.args.get("department", "all")
    status = request.args.get("status", "all")

    students = get_users_by_role("student", search_query=q, department_filter=department, status_filter=status)
    return render_template(
        "manage_students.html",
        students=students,
        search_query=q,
        selected_department=department,
        selected_status=status
    )


@admin_bp.route("/staff")
@login_required
@role_required("admin")
def manage_staff():
    """Staff management page with search, filter, and account status toggle."""
    q = request.args.get("q", "")
    department = request.args.get("department", "all")
    status = request.args.get("status", "all")

    staff_list = get_users_by_role("staff", search_query=q, department_filter=department, status_filter=status)
    return render_template(
        "manage_staff.html",
        staff_list=staff_list,
        search_query=q,
        selected_department=department,
        selected_status=status
    )


@admin_bp.route("/parents")
@login_required
@role_required("admin")
def manage_parents():
    """Parent management page with search, filter, and account status toggle."""
    q = request.args.get("q", "")
    status = request.args.get("status", "all")

    parents = get_users_by_role("parent", search_query=q, status_filter=status)
    return render_template(
        "manage_parents.html",
        parents=parents,
        search_query=q,
        selected_status=status
    )


@admin_bp.route("/create-account", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_account():
    """Form to provision new student, staff, or parent accounts."""
    if request.method == "POST":
        admin_uid = session.get("user", {}).get("uid", "admin")
        role = request.form.get("role", "").strip()
        user_id = request.form.get("user_id", "").strip()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        department = request.form.get("department", "").strip()
        class_name = request.form.get("class_name", "").strip()

        # Parse parent student IDs if parent role
        parent_student_ids = []
        if role == "parent":
            raw_ids = request.form.get("parent_student_ids", "")
            parent_student_ids = [s.strip() for s in raw_ids.split(",") if s.strip()]

        success, message = create_new_account(
            admin_uid=admin_uid,
            role=role,
            user_id=user_id,
            full_name=full_name,
            password=password,
            email=email,
            phone=phone,
            department=department,
            class_name=class_name,
            parent_student_ids=parent_student_ids
        )

        if success:
            flash(message, "success")
            if role == "student":
                return redirect(url_for("admin.manage_students"))
            elif role == "staff":
                return redirect(url_for("admin.manage_staff"))
            elif role == "parent":
                return redirect(url_for("admin.manage_parents"))
            return redirect(url_for("admin.dashboard"))
        else:
            flash(message, "danger")
            form_data = {
                "role": role,
                "user_id": user_id,
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "department": department,
                "class_name": class_name,
                "parent_student_ids": request.form.get("parent_student_ids", "")
            }
            return render_template("create_account.html", form_data=form_data)

    initial_role = request.args.get("role", "student")
    return render_template("create_account.html", form_data={"role": initial_role})


@admin_bp.route("/users/<uid>/edit", methods=["POST"])
@login_required
@role_required("admin")
def edit_user(uid):
    """Updates permitted profile information for a user."""
    update_data = {
        "full_name": request.form.get("full_name", "").strip(),
        "email": request.form.get("email", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "department": request.form.get("department", "").strip(),
        "class_name": request.form.get("class_name", "").strip(),
    }

    if "parent_student_ids" in request.form:
        raw_ids = request.form.get("parent_student_ids", "")
        update_data["parent_student_ids"] = [s.strip() for s in raw_ids.split(",") if s.strip()]

    success, message = update_user_profile(uid, update_data)
    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(request.referrer or url_for("admin.dashboard"))


@admin_bp.route("/users/<uid>/status", methods=["POST"])
@login_required
@role_required("admin")
def change_status(uid):
    """Activates or deactivates an account."""
    new_status = request.form.get("status", "").strip().lower()
    success, message = toggle_user_status(uid, new_status)

    if success:
        flash(message, "success")
    else:
        flash(message, "danger")

    return redirect(request.referrer or url_for("admin.dashboard"))
