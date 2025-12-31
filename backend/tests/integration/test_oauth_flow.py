import importlib
import sys
import asyncio
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException


@pytest.fixture
def oauth_modules(monkeypatch):
    """OAuth 관련 모듈을 테스트 환경으로 재로딩한다."""

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
    monkeypatch.setenv("GOOGLE_FORCE_PROMPT_CONSENT", "false")
    monkeypatch.setenv("FRONTEND_URL", "http://frontend")
    monkeypatch.setenv("ANYIO_BACKEND", "asyncio")

    import app.variable

    monkeypatch.setattr(
        "sqlalchemy.ext.asyncio.create_async_engine", lambda *a, **k: SimpleNamespace()
    )

    importlib.reload(app.variable)

    import app.services.google_oauth_service as google_service
    import app.services.user_service as user_service
    import app.utils.jwt as jwt_utils
    import app.routes.user_route as user_route

    google_service = importlib.reload(google_service)
    user_service = importlib.reload(user_service)
    jwt_utils = importlib.reload(jwt_utils)
    user_route = importlib.reload(user_route)

    return SimpleNamespace(
        google_service=google_service,
        user_service=user_service,
        jwt_utils=jwt_utils,
        user_route=user_route,
    )


def test_google_login_returns_composed_url(oauth_modules):
    response = asyncio.run(oauth_modules.user_route.google_login())

    auth_url = response["auth_url"]
    query = parse_qs(urlparse(auth_url).query)

    assert query["client_id"] == ["client"]
    assert query["redirect_uri"] == ["http://localhost/callback"]
    assert query["scope"] == [
        "openid email profile https://www.googleapis.com/auth/calendar.events.readonly"
    ]
    assert query["access_type"] == ["offline"]
    assert query["include_granted_scopes"] == ["true"]


def test_google_callback_success_returns_redirect(oauth_modules, monkeypatch):
    google_service = oauth_modules.google_service
    user_service = oauth_modules.user_service
    monkeypatch.setattr(
        google_service.GoogleOAuthService,
        "exchange_code_for_tokens",
        staticmethod(
            lambda code: {"access_token": "access", "refresh_token": "refresh"}
        ),
    )
    monkeypatch.setattr(
        google_service.GoogleOAuthService,
        "get_user_info",
        staticmethod(
            lambda token: {
                "google_id": "gid",
                "email": "user@example.com",
                "name": "User",
            }
        ),
    )
    monkeypatch.setattr(
        user_service.UserService,
        "get_or_create_user",
        AsyncMock(return_value=SimpleNamespace(user_id="gid")),
    )
    monkeypatch.setattr(
        oauth_modules.user_route, "create_access_token", lambda data: "jwt-token"
    )

    redirect = asyncio.run(
        oauth_modules.user_route.google_callback("auth-code", db=SimpleNamespace())
    )

    assert redirect.status_code == 302
    assert (
        redirect.headers["location"]
        == "http://frontend/auth/callback?access_token=jwt-token"
    )


def test_google_callback_propagates_http_exception(oauth_modules, monkeypatch):
    google_service = oauth_modules.google_service

    def _raise_http_exc(code: str):
        raise HTTPException(status_code=400, detail="invalid code")

    monkeypatch.setattr(
        google_service.GoogleOAuthService,
        "exchange_code_for_tokens",
        staticmethod(_raise_http_exc),
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            oauth_modules.user_route.google_callback("bad", db=SimpleNamespace())
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "invalid code"


def test_google_callback_wraps_unexpected_error(oauth_modules, monkeypatch):
    google_service = oauth_modules.google_service
    user_service = oauth_modules.user_service

    monkeypatch.setattr(
        google_service.GoogleOAuthService,
        "exchange_code_for_tokens",
        staticmethod(lambda code: {"access_token": "a", "refresh_token": "r"}),
    )
    monkeypatch.setattr(
        google_service.GoogleOAuthService,
        "get_user_info",
        staticmethod(
            lambda token: {
                "google_id": "gid",
                "email": "user@example.com",
                "name": "User",
            }
        ),
    )

    async def _raise(*args, **kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(user_service.UserService, "get_or_create_user", _raise)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            oauth_modules.user_route.google_callback("code", db=SimpleNamespace())
        )

    assert exc.value.status_code == 500
    assert exc.value.detail == "로그인 처리 중 오류: db down"
