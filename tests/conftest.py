import pytest
from unittest.mock import MagicMock, patch
from app import create_app
from app.config import TestingConfig


@pytest.fixture
def app():
    """Create and configure a testing Flask app instance."""
    app = create_app("testing")
    return app


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Flask test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def mock_firestore():
    """Provides a mocked Firestore database client."""
    mock_db = MagicMock()
    return mock_db


@pytest.fixture
def mock_auth_admin():
    """Provides a mocked Firebase Auth Admin SDK."""
    mock_auth = MagicMock()
    return mock_auth
