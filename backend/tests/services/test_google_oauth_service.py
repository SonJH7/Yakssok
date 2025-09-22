import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException


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
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost/callback")
    import app.variable  # noqa: F401

    importlib.reload(app.variable)
    import app.services.google_oauth_service  # noqa: F401

    importlib.reload(app.services.google_oauth_service)


def test_generate_auth_url_contains_parameters():
    from app.services.google_oauth_service import GoogleOAuthService

    url = GoogleOAuthService.generate_auth_url()
    assert "client_id=client" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%2Fcallback" in url
    assert "scope=openid+email+profile" in url


def test_exchange_code_for_tokens_success(monkeypatch):
    from app.services.google_oauth_service import GoogleOAuthService

    def mock_post(url, data):
        assert "oauth2.googleapis.com/token" in url
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"access_token": "access", "refresh_token": "refresh"},
        )

    monkeypatch.setattr("requests.post", mock_post)
    tokens = GoogleOAuthService.exchange_code_for_tokens("auth-code")

    assert tokens == {"access_token": "access", "refresh_token": "refresh"}


@pytest.mark.parametrize(
    "response_json",
    [
        {"refresh_token": "refresh"},
        {},
    ],
)
def test_exchange_code_for_tokens_missing_access_token(response_json, monkeypatch):
    from app.services.google_oauth_service import GoogleOAuthService

    def mock_post(url, data):
        return SimpleNamespace(
            raise_for_status=lambda: None, json=lambda: response_json
        )

    monkeypatch.setattr("requests.post", mock_post)

    with pytest.raises(HTTPException) as exc:
        GoogleOAuthService.exchange_code_for_tokens("code")

    assert exc.value.status_code == 400


def test_exchange_code_for_tokens_request_failure(monkeypatch):
    from app.services.google_oauth_service import GoogleOAuthService

    def mock_post(url, data):
        raise requests.RequestException("boom")

    import requests

    monkeypatch.setattr("requests.post", mock_post)

    with pytest.raises(HTTPException) as exc:
        GoogleOAuthService.exchange_code_for_tokens("code")

    assert exc.value.status_code == 500


def test_get_user_info_success(monkeypatch):
    from app.services.google_oauth_service import GoogleOAuthService

    def mock_get(url):
        assert "userinfo" in url
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"id": "123", "email": "user@example.com", "name": "User"},
        )

    monkeypatch.setattr("requests.get", mock_get)
    user_info = GoogleOAuthService.get_user_info("token")

    assert user_info == {
        "google_id": "123",
        "email": "user@example.com",
        "name": "User",
    }


@pytest.mark.parametrize(
    "response_json",
    [
        {"email": "user@example.com"},
        {"id": "123"},
        {},
    ],
)
def test_get_user_info_missing_fields(monkeypatch, response_json):
    from app.services.google_oauth_service import GoogleOAuthService

    def mock_get(url):
        return SimpleNamespace(
            raise_for_status=lambda: None, json=lambda: response_json
        )

    monkeypatch.setattr("requests.get", mock_get)

    with pytest.raises(HTTPException) as exc:
        GoogleOAuthService.get_user_info("token")

    assert exc.value.status_code == 400


def test_get_user_info_request_failure(monkeypatch):
    from app.services.google_oauth_service import GoogleOAuthService
    import requests

    def mock_get(url):
        raise requests.RequestException("boom")

    monkeypatch.setattr("requests.get", mock_get)

    with pytest.raises(HTTPException) as exc:
        GoogleOAuthService.get_user_info("token")

    assert exc.value.status_code == 500
