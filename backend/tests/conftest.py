"""Test configuration.

The settings are read when the application modules are imported, so they are
set here, before any `app.*` import: an isolated SQLite file and a test-only
signing key.
"""

import os
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="finguard-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["JWT_SECRET_KEY"] = "unit-test-signing-key-0123456789-abcdefgh"
# The AI client is created at import time; no request is sent during tests.
os.environ["GROQ_API_KEY"] = "placeholder-key-never-used-in-tests"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.models  # noqa: E402,F401  (registers every table)
from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def schema():
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    return TestClient(app)
