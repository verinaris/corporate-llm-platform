"""
Gemeinsame Test-Fixtures.

Nutzt eine In-Memory-SQLite-DB für Tests, damit echte Daten unangetastet
bleiben.
"""

import os

# Dummy-Settings setzen, BEVOR Module geladen werden
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-dummy-for-tests")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-production")
os.environ.setdefault("DATABASE_URL", "sqlite:///./data/test_platform.db")
os.environ.setdefault("BOOTSTRAP_ADMIN_EMAIL", "")
os.environ.setdefault("BOOTSTRAP_ADMIN_PASSWORD", "")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session, SQLModel, select  # noqa: E402

from app.auth.passwords import hash_password  # noqa: E402
from app.database import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User, UserBranch, UserRole  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _setup_test_db():
    """Vor allen Tests: Tabellen anlegen. Danach: aufräumen."""
    SQLModel.metadata.create_all(engine)
    yield
    # Test-DB nach den Tests entfernen
    import os
    from pathlib import Path

    db_file = Path("./data/test_platform.db")
    if db_file.exists():
        try:
            os.remove(db_file)
        except OSError:
            pass


@pytest.fixture(autouse=True)
def _clean_users():
    """Vor jedem Test: User-Tabelle leeren."""
    with Session(engine) as session:
        for user in session.exec(select(User)).all():
            session.delete(user)
        session.commit()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_user() -> User:
    """Erzeugt einen Admin-User in der Test-DB."""
    with Session(engine) as session:
        user = User(
            email="admin@test.local",
            password_hash=hash_password("AdminPass123!"),
            role=UserRole.ADMIN,
            branch=UserBranch.GENERIC,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


@pytest.fixture
def regular_user() -> User:
    """Erzeugt einen normalen User in der Test-DB."""
    with Session(engine) as session:
        user = User(
            email="user@test.local",
            password_hash=hash_password("UserPass123!"),
            role=UserRole.USER,
            branch=UserBranch.GENERIC,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def _login(client: TestClient, email: str, password: str) -> str:
    """Helper: loggt einen User ein und gibt den Token zurück."""
    r = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    assert r.status_code == 200, f"Login failed: {r.json()}"
    return r.json()["access_token"]


@pytest.fixture
def admin_token(client, admin_user) -> str:
    return _login(client, "admin@test.local", "AdminPass123!")


@pytest.fixture
def user_token(client, regular_user) -> str:
    return _login(client, "user@test.local", "UserPass123!")
