import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

# Lets the tests import main.py from the backend folder
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

# main.py creates a database file the moment it is imported. Importing it from inside a
# temporary folder keeps that file out of your project and away from your real issues.db.
with tempfile.TemporaryDirectory() as _temp_dir:
    _previous_dir = os.getcwd()
    os.chdir(_temp_dir)
    try:
        import main  # noqa: E402,F401
    finally:
        os.chdir(_previous_dir)

TEST_ADMIN_KEY = "test-admin-key"


@pytest.fixture
def anon_client(tmp_path, monkeypatch):
    """A visitor who is not logged in. Every test gets its own empty database."""
    monkeypatch.setattr(main, "DB_FILE", str(tmp_path / "test.db"))
    # Replaces any real ADMIN_KEY from your .env, so tests never depend on your own key
    monkeypatch.setenv("ADMIN_KEY", TEST_ADMIN_KEY)
    main.init_db()
    return TestClient(main.app)


@pytest.fixture
def client(anon_client):
    """A logged-in admin: same app and database, but every request carries the admin key."""
    return TestClient(main.app, headers={"X-Admin-Key": TEST_ADMIN_KEY})