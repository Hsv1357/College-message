from unittest.mock import MagicMock, patch
from app.firebase_client import (
    normalize_user_id,
    get_internal_auth_email,
    get_initialization_status,
    is_firebase_initialized,
    init_firebase,
)
from app.admin.services import (
    get_dashboard_statistics,
    get_users_by_role,
    create_new_account,
    update_user_profile,
    toggle_user_status,
)


def test_user_id_normalization():
    """Verify consistent normalization of User IDs."""
    assert normalize_user_id("Admin-2004") == "admin-2004"
    assert normalize_user_id("  STU-1001  ") == "stu-1001"
    assert normalize_user_id("") == ""
    assert normalize_user_id(None) == ""


def test_deterministic_internal_auth_email():
    """Verify deterministic, collision-safe internal auth email derivation."""
    assert get_internal_auth_email("Admin-2004") == "admin-2004@auth.campusconnect.internal"
    assert get_internal_auth_email("STU-1001") == "stu-1001@auth.campusconnect.internal"


def test_missing_firebase_configuration_handling():
    """Test 12: Missing Firebase configuration reports clear, actionable status without crashing."""
    status = get_initialization_status()
    assert "initialized" in status
    assert "error" in status
    # If service account is missing, initialized should be False and error provided
    if not status["initialized"]:
        assert status["error"] is not None
        assert "service account" in status["error"].lower()


def test_get_users_by_role_filters_accurately():
    """Test 9: Verify user query strictly returns only users for the requested role."""
    mock_doc1 = MagicMock()
    mock_doc1.id = "uid-1"
    mock_doc1.to_dict.return_value = {
        "user_id": "STU-001",
        "full_name": "Student One",
        "role": "student",
        "department": "Computer Science",
        "account_status": "active"
    }

    mock_doc2 = MagicMock()
    mock_doc2.id = "uid-2"
    mock_doc2.to_dict.return_value = {
        "user_id": "STU-002",
        "full_name": "Student Two",
        "role": "student",
        "department": "Mechanical Engineering",
        "account_status": "disabled"
    }

    with patch("app.admin.services.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_query = MagicMock()
        mock_db.collection.return_value.where.return_value = mock_query
        mock_query.stream.return_value = [mock_doc1, mock_doc2]

        # 1. Fetch all students
        students = get_users_by_role("student")
        assert len(students) == 2
        assert students[0]["user_id"] == "STU-001"

        # 2. Filter by search query
        students_search = get_users_by_role("student", search_query="Two")
        assert len(students_search) == 1
        assert students_search[0]["user_id"] == "STU-002"

        # 3. Filter by department
        students_dept = get_users_by_role("student", department_filter="Computer Science")
        assert len(students_dept) == 1
        assert students_dept[0]["user_id"] == "STU-001"

        # 4. Filter by status
        students_active = get_users_by_role("student", status_filter="active")
        assert len(students_active) == 1
        assert students_active[0]["user_id"] == "STU-001"


def test_dashboard_statistics_calculation():
    """Verify statistics computation from Firestore stream."""
    docs = [
        MagicMock(to_dict=lambda: {"role": "student", "account_status": "active"}),
        MagicMock(to_dict=lambda: {"role": "student", "account_status": "disabled"}),
        MagicMock(to_dict=lambda: {"role": "staff", "account_status": "active"}),
        MagicMock(to_dict=lambda: {"role": "parent", "account_status": "active"}),
    ]

    with patch("app.admin.services.get_db") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.collection.return_value.stream.return_value = docs

        stats = get_dashboard_statistics()

        assert stats["total_students"] == 2
        assert stats["total_staff"] == 1
        assert stats["total_parents"] == 1
        assert stats["active_accounts"] == 3
        assert stats["disabled_accounts"] == 1
        assert stats["total_accounts"] == 4


def test_account_creation_validation_rules():
    """Verify validation constraints: short password, empty user ID, invalid role."""
    with patch("app.admin.services.get_db"), patch("app.admin.services.get_auth_admin"):
        # Invalid role
        ok, msg = create_new_account("admin", "hacker", "USER-1", "Name", "password123")
        assert not ok
        assert "Invalid role" in msg

        # Empty user id
        ok, msg = create_new_account("admin", "student", "", "Name", "password123")
        assert not ok
        assert "User ID cannot be empty" in msg

        # Empty full name
        ok, msg = create_new_account("admin", "student", "STU-1", "   ", "password123")
        assert not ok
        assert "Full Name cannot be empty" in msg

        # Short password (<6 chars)
        ok, msg = create_new_account("admin", "student", "STU-1", "Name", "123")
        assert not ok
        assert "at least 6 characters" in msg
