import importlib
import sys
from datetime import timedelta
from pathlib import Path

import pytest
from jose import jwt


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    root_dir = Path(__file__).resolve().parents[2]
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_MINUTES", "120")
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URL_USER", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost")
    import app.variable  # noqa: F401

    importlib.reload(app.variable)
    import app.utils.jwt  # noqa: F401

    importlib.reload(app.utils.jwt)


def test_create_access_token_default_expiry():
    from app.utils.jwt import create_access_token

    token = create_access_token({"sub": "user123"})
    decoded = jwt.decode(token, "test-secret", algorithms=["HS256"])

    assert decoded["sub"] == "user123"
    assert "exp" in decoded


def test_create_access_token_custom_expiry():
    from app.utils.jwt import create_access_token

    token = create_access_token({"sub": "user456"}, expires_delta=timedelta(minutes=5))
    decoded = jwt.decode(token, "test-secret", algorithms=["HS256"])

    assert decoded["sub"] == "user456"


def test_verify_token_invalid_returns_none():
    from app.utils.jwt import verify_token

    invalid_token = jwt.encode(
        {"sub": "user789"}, "different-secret", algorithm="HS256"
    )
    assert verify_token(invalid_token) is None


def test_verify_token_valid_returns_payload():
    from app.utils.jwt import create_access_token, verify_token

    token = create_access_token({"sub": "valid-user"})
    payload = verify_token(token)

    assert payload is not None
    assert payload["sub"] == "valid-user"


def test_verify_token_expired_returns_none():
    from app.utils.jwt import create_access_token, verify_token

    expired_token = create_access_token(
        {"sub": "expired-user"}, expires_delta=timedelta(minutes=-1)
    )

    assert verify_token(expired_token) is None
