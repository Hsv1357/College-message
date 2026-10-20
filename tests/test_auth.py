from unittest.mock import patch, MagicMock
from flask import session


def test_login_page_loads(client):
    """Test 1: Verify login page renders properly with 200 OK."""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"CampusConnect" in response.data
    assert b"User ID" in response.data
    assert b"Password" in response.data


def test_missing_login_fields_rejected(client):
    """Test 2: Verify missing User ID or password is rejected."""
    # Empty form
    resp1 = client.post("/login", data={"user_id": "", "password": ""}, follow_redirects=True)
    assert b"Please enter both User ID and Password" in resp1.data

    # Missing password
    resp2 = client.post("/login", data={"user_id": "Admin-2004", "password": ""}, follow_redirects=True)
    assert b"Please enter both User ID and Password" in resp2.data

    # Missing user_id
    resp3 = client.post("/login", data={"user_id": "", "password": "anypassword"}, follow_redirects=True)
    assert b"Please enter both User ID and Password" in resp3.data


def test_invalid_credentials_handled_correctly(client):
    """Test 3: Verify invalid credentials return uniform safe error."""
    with patch("app.auth.routes.authenticate_user") as mock_auth:
        mock_auth.return_value = (
            False,
            "Login failed. Please check your credentials or contact the administrator.",
            None
        )

        response = client.post(
            "/login",
            data={"user_id": "WrongUser", "password": "WrongPassword"},
            follow_redirects=True
        )

        assert response.status_code == 200
        assert b"Login failed. Please check your credentials" in response.data


def test_successful_admin_login(client):
    """Verify admin login establishes session and redirects to admin dashboard."""
    mock_profile = {
        "uid": "admin-uid-123",
        "user_id": "Admin-2004",
        "full_name": "System Administrator",
        "role": "admin",
        "email": "admin@campusconnect.local",
        "account_status": "active"
    }

    with patch("app.auth.routes.authenticate_user") as mock_auth:
        mock_auth.return_value = (True, "Login successful.", mock_profile)

        response = client.post(
            "/login",
            data={"user_id": "Admin-2004", "password": "admin@Test123"},
            follow_redirects=False
        )

        assert response.status_code == 302
        assert "/admin/dashboard" in response.headers["Location"]

        with client.session_transaction() as sess:
            assert sess["user"]["user_id"] == "Admin-2004"
            assert sess["user"]["role"] == "admin"


def test_successful_student_login(client):
    """Verify student login redirects to role dashboard."""
    mock_profile = {
        "uid": "student-uid-456",
        "user_id": "STU-1001",
        "full_name": "Alice Student",
        "role": "student",
        "email": "alice@college.edu",
        "account_status": "active"
    }

    with patch("app.auth.routes.authenticate_user") as mock_auth:
        mock_auth.return_value = (True, "Login successful.", mock_profile)

        response = client.post(
            "/login",
            data={"user_id": "STU-1001", "password": "password123"},
            follow_redirects=False
        )

        assert response.status_code == 302
        assert "/role/dashboard" in response.headers["Location"]

        with client.session_transaction() as sess:
            assert sess["user"]["user_id"] == "STU-1001"
            assert sess["user"]["role"] == "student"


def test_disabled_account_cannot_login(client):
    """Test 10: Verify deactivated accounts are prevented from logging in."""
    with patch("app.auth.routes.authenticate_user") as mock_auth:
        mock_auth.return_value = (
            False,
            "Your account has been deactivated. Please contact the administrator.",
            None
        )

        response = client.post(
            "/login",
            data={"user_id": "DisabledUser", "password": "somePassword"},
            follow_redirects=True
        )

        assert response.status_code == 200
        assert b"Your account has been deactivated" in response.data

        with client.session_transaction() as sess:
            assert "user" not in sess


def test_logout_ends_application_session(client):
    """Test 11: Verify logout clears session and redirects to login."""
    with client.session_transaction() as sess:
        sess["user"] = {
            "uid": "test-uid",
            "user_id": "Admin-2004",
            "role": "admin",
            "full_name": "Administrator"
        }

    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"You have been logged out safely" in response.data

    with client.session_transaction() as sess:
        assert "user" not in sess
