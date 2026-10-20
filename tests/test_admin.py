from unittest.mock import patch


def test_unauthenticated_cannot_access_admin_dashboard(client):
    """Test 4: Unauthenticated requests to /admin/dashboard redirect to login."""
    response = client.get("/admin/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_non_admin_cannot_access_admin_endpoints(client):
    """Test 5: Students, staff, and parents are blocked from admin-only routes."""
    # Simulate logged-in student
    with client.session_transaction() as sess:
        sess["user"] = {
            "uid": "student-1",
            "user_id": "STU-1001",
            "role": "student",
            "full_name": "Student User"
        }

    admin_routes = [
        "/admin/dashboard",
        "/admin/students",
        "/admin/staff",
        "/admin/parents",
        "/admin/create-account",
    ]

    for route in admin_routes:
        resp = client.get(route, follow_redirects=True)
        # Should be redirected away with flash error
        assert b"Unauthorized access" in resp.data


def test_admin_can_access_management_pages(client):
    """Test 6: Authenticated administrator can access all management views."""
    with client.session_transaction() as sess:
        sess["user"] = {
            "uid": "admin-1",
            "user_id": "Admin-2004",
            "role": "admin",
            "full_name": "System Administrator"
        }

    with patch("app.admin.routes.get_dashboard_statistics") as mock_stats, \
         patch("app.admin.routes.get_users_by_role") as mock_users:

        mock_stats.return_value = {
            "total_students": 5,
            "total_staff": 2,
            "total_parents": 3,
            "active_accounts": 10,
            "disabled_accounts": 0,
            "total_accounts": 10
        }
        mock_users.return_value = []

        # 1. Admin Dashboard
        resp1 = client.get("/admin/dashboard")
        assert resp1.status_code == 200
        assert b"Administrator Dashboard" in resp1.data

        # 2. Manage Students
        resp2 = client.get("/admin/students")
        assert resp2.status_code == 200
        assert b"Student Management" in resp2.data

        # 3. Manage Staff
        resp3 = client.get("/admin/staff")
        assert resp3.status_code == 200
        assert b"Staff Management" in resp3.data

        # 4. Manage Parents
        resp4 = client.get("/admin/parents")
        assert resp4.status_code == 200
        assert b"Parent Management" in resp4.data

        # 5. Create Account
        resp5 = client.get("/admin/create-account")
        assert resp5.status_code == 200
        assert b"Provision New Account" in resp5.data


def test_admin_can_change_account_status(client):
    """Test: Admin can activate or deactivate account status."""
    with client.session_transaction() as sess:
        sess["user"] = {
            "uid": "admin-1",
            "user_id": "Admin-2004",
            "role": "admin",
            "full_name": "Admin"
        }

    with patch("app.admin.routes.toggle_user_status") as mock_toggle:
        mock_toggle.return_value = (True, "Account has been successfully deactivated.")

        resp = client.post(
            "/admin/users/target-uid-123/status",
            data={"status": "disabled"},
            follow_redirects=True
        )

        assert resp.status_code == 200
        mock_toggle.assert_called_once_with("target-uid-123", "disabled")


def test_admin_can_edit_user_profile(client):
    """Test: Admin can update editable fields of user profile."""
    with client.session_transaction() as sess:
        sess["user"] = {
            "uid": "admin-1",
            "user_id": "Admin-2004",
            "role": "admin",
            "full_name": "Admin"
        }

    with patch("app.admin.routes.update_user_profile") as mock_update:
        mock_update.return_value = (True, "Profile updated successfully.")

        resp = client.post(
            "/admin/users/target-uid-123/edit",
            data={
                "full_name": "Updated Name",
                "email": "updated@college.edu",
                "phone": "555-1234",
                "department": "Computer Science",
                "class_name": "Year 2"
            },
            follow_redirects=True
        )

        assert resp.status_code == 200
        assert mock_update.called
