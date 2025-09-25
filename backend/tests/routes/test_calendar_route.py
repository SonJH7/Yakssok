import asyncio
import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.responses import JSONResponse


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    root_dir = Path(__file__).resolve().parents[2]
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

    monkeypatch.setenv("SECRET_KEY", "secret")
    monkeypatch.setenv("ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URL_USER", "sqlite+aiosqlite:///:memory:")

    import app.variable

    importlib.reload(app.variable)


@pytest.fixture
def route_module(monkeypatch):
    import app.routes.calendar_route as calendar_route

    calendar_route = importlib.reload(calendar_route)

    return calendar_route


def test_requires_jwt_header(route_module):
    with pytest.raises(HTTPException) as exc:
        asyncio.run(route_module.list_events(credentials=None))

    assert exc.value.status_code == 401


def test_missing_refresh_token_returns_scope_error(route_module, monkeypatch):
    monkeypatch.setattr(route_module, "verify_token", lambda token: {"sub": "user"})

    async def _get_user(*args, **kwargs):
        return SimpleNamespace(google_refresh_token="")

    monkeypatch.setattr(route_module.UserService, "get_user_by_google_id", _get_user)

    response = asyncio.run(
        route_module.list_events(
            db=SimpleNamespace(),
            credentials=SimpleNamespace(scheme="Bearer", credentials="jwt"),
        )
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert (
        response.body
        == b'{"code":"calendar_scope_missing","reauthUrl":"/user/google/login?force=1"}'
    )


def test_successful_event_fetch(route_module, monkeypatch):
    monkeypatch.setattr(route_module, "verify_token", lambda token: {"sub": "user"})

    async def _get_user(*args, **kwargs):
        return SimpleNamespace(google_refresh_token="refresh")

    monkeypatch.setattr(route_module.UserService, "get_user_by_google_id", _get_user)
    monkeypatch.setattr(
        route_module.GoogleCalendarService,
        "refresh_access_token",
        lambda refresh: "access",
    )
    monkeypatch.setattr(
        route_module.GoogleCalendarService,
        "list_primary_events",
        lambda *a, **k: {"events": [1, 2], "nextPageToken": "next"},
    )

    result = asyncio.run(
        route_module.list_events(
            db=SimpleNamespace(),
            credentials=SimpleNamespace(scheme="Bearer", credentials="jwt"),
            max_results=10,
        )
    )

    assert result == {"events": [1, 2], "nextPageToken": "next"}


def test_invalid_grant_triggers_reauth(route_module, monkeypatch):
    monkeypatch.setattr(route_module, "verify_token", lambda token: {"sub": "user"})

    async def _get_user(*args, **kwargs):
        return SimpleNamespace(google_refresh_token="refresh")

    monkeypatch.setattr(route_module.UserService, "get_user_by_google_id", _get_user)

    def _raise_invalid_grant(refresh):
        raise HTTPException(status_code=401, detail="invalid_grant")

    monkeypatch.setattr(
        route_module.GoogleCalendarService,
        "refresh_access_token",
        _raise_invalid_grant,
    )

    response = asyncio.run(
        route_module.list_events(
            db=SimpleNamespace(),
            credentials=SimpleNamespace(scheme="Bearer", credentials="jwt"),
        )
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 401
    assert (
        response.body
        == b'{"code":"calendar_refresh_failed","reauthUrl":"/user/google/login?force=1"}'
    )
