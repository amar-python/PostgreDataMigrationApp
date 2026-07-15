"""Shared test fixtures for all MEP backend tests.

Uses an in-memory SQLite database so tests run without PostgreSQL.
All test modules share the same engine/session/client to avoid
conflicting dependency overrides on the FastAPI app.
"""
import os
import shutil
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from database.connection import get_db
from main import app

# ---------------------------------------------------------------------------
# Single shared test database
# ---------------------------------------------------------------------------

SQLALCHEMY_TEST_URL = "sqlite:///./test_mep_shared.db"
test_engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

# Shared temporary upload directory
TEST_UPLOAD_DIR = tempfile.mkdtemp(prefix="mep_test_shared_")


def _override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


# Apply once — all test modules use this override
app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=test_engine)
    os.environ["MEP_UPLOAD_DIR"] = TEST_UPLOAD_DIR
    os.environ["MEP_REPORT_DIR"] = os.path.join(TEST_UPLOAD_DIR, "reports")
    yield
    Base.metadata.drop_all(bind=test_engine)
    # Clean up upload/report files
    if os.path.isdir(TEST_UPLOAD_DIR):
        shutil.rmtree(TEST_UPLOAD_DIR, ignore_errors=True)
        os.makedirs(TEST_UPLOAD_DIR, exist_ok=True)


@pytest.fixture
def client():
    """Return a TestClient for the FastAPI app."""
    return TestClient(app)
