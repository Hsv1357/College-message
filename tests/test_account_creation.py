from unittest.mock import patch


def test_admin_can_create_student_account(client):
    """Test 7a: Administrator successfully provisions a student account."""
    with client.session_transaction() as sess:
        sess["user"] = {
            "uid": "admin-1",
            "user_id": "Admin-2004",
            "role": "admin",
            "full_name": "Admin"
        }

    with patch("app.admin.routes.create_new_account") as mock_create:
        mock_create.return_value = (True, "Successfully created Student account for 'STU-1001'.")

        response = client.post(
            "/admin/create-account",
            data={
                "role": "student",
                "user_id": "STU-1001",
                "full_name": "Alice Wonderland",
                "password": "Password@123",
                "email": "alice@college.edu",
                "department": "Computer Science",
                "class_name": "Section A"
            },
            follow_redirects=False
        )

        assert response.status_code == 302
        assert "/admin/students" in response.headers["Location"]
        assert mock_create.called


def test_admin_can_create_staff_account(client):
    """Test 7b: Administrator successfully provisions a staff account."""
    with client.session_transaction() as sess:
        sess["user"] = {
            "uid": "admin-1",
            "user_id": "Admin-2004",
            "role": "admin",
            "full_name": "Admin"
        }

    with patch("app.admin.routes.create_new_account") as mock_create:
        mock_create.return_value = (True, "Successfully created Staff account for 'STF-201'.")

        response = client.post(
            "/admin/create-account",
            data={
                "role": "staff",
                "user_id": "STF-201",
                "full_name": "Dr. Robert Smith",
                "password": "StaffPassword@123",
                "email": "robert@college.edu",
                "department": "Mechanical Engineering"
            },
            follow_redirects=False
        )

        assert response.status_code == 302
        assert "/admin/staff" in response.headers["Location"]


def test_admin_can_create_parent_account(client):
    """Test 7c: Administrator successfully provisions a parent account with linked students."""
    with client.session_transaction() as sess:
        sess["user"] = {
            "uid": "admin-1",
            "user_id": "Admin-2004",
            "role": "admin",
            "full_name": "Admin"
        }

    with patch("app.admin.routes.create_new_account") as mock_create:
        mock_create.return_value = (True, "Successfully created Parent account for 'PAR-301'.")

        response = client.post(
            "/admin/create-account",
            data={
                "role": "parent",
                "user_id": "PAR-301",
                "full_name": "Mary Wonderland",
                "password": "ParentPassword@123",
                "email": "mary@example.com",
                "parent_student_ids": "STU-1001, STU-1002"
            },
            follow_redirects=False
        )

        assert response.status_code == 302
        assert "/admin/parents" in response.headers["Location"]


def test_duplicate_user_ids_are_rejected(client):
    """Test 8: System rejects duplicate User IDs during account creation."""
    with client.session_transaction() as sess:
        sess["user"] = {
            "uid": "admin-1",
            "user_id": "Admin-2004",
            "role": "admin",
            "full_name": "Admin"
        }

    with patch("app.admin.routes.create_new_account") as mock_create:
        mock_create.return_value = (False, "User ID 'STU-1001' is already registered.")

        response = client.post(
            "/admin/create-account",
            data={
                "role": "student",
                "user_id": "STU-1001",
                "full_name": "Duplicate Student",
                "password": "Password@123",
            },
            follow_redirects=True
        )

        assert response.status_code == 200
        assert b"is already registered" in response.data
