
import os
import sys
import tempfile

import pytest
from fastapi.testclient import TestClient

# Lets the tests import main.py from the backend folder
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

# Keep the database created during import out of your project
with tempfile.TemporaryDirectory() as _temp_dir:
    _previous_dir = os.getcwd()
    os.chdir(_temp_dir)
    try:
        import main  # noqa: E402,F401
    finally:
        os.chdir(_previous_dir)


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Every test gets its own empty database
    monkeypatch.setattr(main, "DB_FILE", str(tmp_path / "test.db"))
    main.init_db()
    return TestClient(main.app)