import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException


@pytest.fixture
def load_google_service(monkeypatch):
    """환경 변수를 구성한 뒤 Google OAuth 서비스를 다시 로드한다."""

    root_dir = Path(__file__).resolve().parents[2]
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

    def _loader(*, force_prompt: bool = False):
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("ALGORITHM", "HS256")
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
        monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_MINUTES", "120")
        monkeypatch.setenv(
            "SQLALCHEMY_DATABASE_URL_USER", "sqlite+aiosqlite:///:memory:"
        )
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "client")
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")
        monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost/callback")
        monkeypatch.setenv(
            "GOOGLE_FORCE_PROMPT_CONSENT", "true" if force_prompt else "false"
        )

        import app.variable  # noqa: F401

        importlib.reload(app.variable)
        import app.services.google_oauth_service  # noqa: F401

        importlib.reload(app.services.google_oauth_service)

        return app.services.google_oauth_service

    return _loader


def test_generate_auth_url_contains_parameters(load_google_service):
    service = load_google_service()

    url = service.GoogleOAuthService.generate_auth_url()
    query = parse_qs(urlparse(url).query)

    assert query["client_id"] == ["client"]
    assert query["redirect_uri"] == ["http://localhost/callback"]
    assert query["scope"] == [
        "openid email profile https://www.googleapis.com/auth/calendar.events.readonly"
    ]
    assert query["access_type"] == ["offline"]
    assert query["include_granted_scopes"] == ["true"]
    assert "prompt" not in query


def test_generate_auth_url_includes_prompt_when_forced(load_google_service):
    service = load_google_service(force_prompt=True)
    url = service.GoogleOAuthService.generate_auth_url()
    query = parse_qs(urlparse(url).query)

    assert query["prompt"] == ["consent"]


def test_exchange_code_for_tokens_success(load_google_service, monkeypatch):
    service = load_google_service()

    def mock_post(url, data):
        assert "oauth2.googleapis.com/token" in url
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"access_token": "access", "refresh_token": "refresh"},
        )

    monkeypatch.setattr("requests.post", mock_post)
    tokens = service.GoogleOAuthService.exchange_code_for_tokens("auth-code")

    assert tokens == {"access_token": "access", "refresh_token": "refresh"}


@pytest.mark.parametrize(
    "response_json",
    [
        {"refresh_token": "refresh"},
        {},
    ],
)
def test_exchange_code_for_tokens_missing_access_token(
    response_json, load_google_service, monkeypatch
):
    service = load_google_service()

    def mock_post(url, data):
        return SimpleNamespace(
            raise_for_status=lambda: None, json=lambda: response_json
        )

    monkeypatch.setattr("requests.post", mock_post)

    with pytest.raises(HTTPException) as exc:
        service.GoogleOAuthService.exchange_code_for_tokens("code")

    assert exc.value.status_code == 400


def test_exchange_code_for_tokens_request_failure(load_google_service, monkeypatch):
    import requests

    service = load_google_service()

    def mock_post(url, data):
        raise requests.RequestException("boom")

    monkeypatch.setattr("requests.post", mock_post)

    with pytest.raises(HTTPException) as exc:
        service.GoogleOAuthService.exchange_code_for_tokens("code")

    assert exc.value.status_code == 500


def test_get_user_info_success(load_google_service, monkeypatch):
    service = load_google_service()

    def mock_get(url):
        assert "userinfo" in url
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"id": "123", "email": "user@example.com", "name": "User"},
        )

    monkeypatch.setattr("requests.get", mock_get)
    user_info = service.GoogleOAuthService.get_user_info("token")

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
def test_get_user_info_missing_fields(load_google_service, monkeypatch, response_json):
    service = load_google_service()

    def mock_get(url):
        return SimpleNamespace(
            raise_for_status=lambda: None, json=lambda: response_json
        )

    monkeypatch.setattr("requests.get", mock_get)

    with pytest.raises(HTTPException) as exc:
        service.GoogleOAuthService.get_user_info("token")

    assert exc.value.status_code == 400


def test_get_user_info_request_failure(load_google_service, monkeypatch):
    import requests

    service = load_google_service()

    def mock_get(url):
        raise requests.RequestException("boom")

    monkeypatch.setattr("requests.get", mock_get)

    with pytest.raises(HTTPException) as exc:
        service.GoogleOAuthService.get_user_info("token")

    assert exc.value.status_code == 500
