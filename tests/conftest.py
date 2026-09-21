import os
import tempfile
from pathlib import Path

import pytest

# Keep API tests away from the developer's running database.
_test_dir = tempfile.TemporaryDirectory(prefix='civicshield-tests-')
os.environ['DATABASE_URL'] = 'sqlite:///' + (Path(_test_dir.name) / 'test.db').as_posix()

from fastapi.testclient import TestClient
from app.main import app
from app.database import engine


def pytest_sessionfinish(session, exitstatus):
    # Release pooled SQLite file handles before TemporaryDirectory cleans up on Windows.
    engine.dispose()
    _test_dir.cleanup()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client
