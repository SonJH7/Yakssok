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

    if "httpx" not in sys.modules:
        import types

        class _StubRequestError(Exception):
            pass

        class _StubAsyncClient:
            def __init__(self, *args, **kwargs):
                raise RuntimeError("httpx not installed")

        stub = types.SimpleNamespace(
            AsyncClient=_StubAsyncClient, RequestError=_StubRequestError
        )
        sys.modules["httpx"] = stub

    monkeypatch.setenv("SECRET_KEY", "secret")
    monkeypatch.setenv("ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URL_USER", "sqlite+aiosqlite:///:memory:")

    import app.variable

    importlib.reload(app.variable)


@pytest.fixture
def route_module():
    import app.routes.calendar_route as module

    reloaded = importlib.reload(module)
    reloaded.GoogleCalendarService._client = None
    return reloaded


def test_requires_jwt_header(route_module):
    with pytest.raises(HTTPException) as exc:
        asyncio.run(route_module.list_events(db=SimpleNamespace(), credentials=None))
    assert exc.value.detail == "인증 토큰이 필요합니다."


def test_missing_refresh_token_returns_scope_error(route_module, monkeypatch):
    monkeypatch.setattr(route_module, "verify_token", lambda token: {"sub": "user"})

    async def _get_user(*args, **kwargs):
        return SimpleNamespace(google_refresh_token=None)

    monkeypatch.setattr(route_module.UserService, "get_user_by_google_id", _get_user)

    response = asyncio.run(
        route_module.list_events(
            db=SimpleNamespace(),
            credentials=SimpleNamespace(scheme="Bearer", credentials="jwt"),
        )
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert response.body == (
        b'{"code":"calendar_scope_missing","reauthUrl":"/user/google/login?force=1"}'
    )


def test_successful_event_fetch(route_module, monkeypatch):
    monkeypatch.setattr(route_module, "verify_token", lambda token: {"sub": "user"})

    async def _get_user(*args, **kwargs):
        return SimpleNamespace(google_refresh_token="refresh")

    monkeypatch.setattr(route_module.UserService, "get_user_by_google_id", _get_user)

    async def _refresh(refresh):
        return "access"

    async def _list(*a, **k):
        return {"events": [1, 2], "nextPageToken": "next"}

    monkeypatch.setattr(
        route_module.GoogleCalendarService, "refresh_access_token", _refresh
    )
    monkeypatch.setattr(
        route_module.GoogleCalendarService, "list_primary_events", _list
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

    async def _raise_invalid_grant(refresh):
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
    assert response.body == (
        b'{"code":"google_reauth_required","reauthUrl":"/user/google/login?force=1"}'
    )


def test_list_events_insufficient_scope(route_module, monkeypatch):
    monkeypatch.setattr(route_module, "verify_token", lambda token: {"sub": "user"})

    async def _get_user(*args, **kwargs):
        return SimpleNamespace(google_refresh_token="refresh")

    monkeypatch.setattr(route_module.UserService, "get_user_by_google_id", _get_user)

    async def _refresh(refresh):
        return "access"

    async def _raise_insufficient(*args, **kwargs):
        raise HTTPException(status_code=403, detail="insufficient_scope")

    monkeypatch.setattr(
        route_module.GoogleCalendarService, "refresh_access_token", _refresh
    )
    monkeypatch.setattr(
        route_module.GoogleCalendarService, "list_primary_events", _raise_insufficient
    )

    response = asyncio.run(
        route_module.list_events(
            db=SimpleNamespace(),
            credentials=SimpleNamespace(scheme="Bearer", credentials="jwt"),
        )
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 403
    assert response.body == (
        b'{"code":"insufficient_scope","reauthUrl":"/user/google/login?force=1"}'
    )


def test_list_events_requires_reauth(route_module, monkeypatch):
    monkeypatch.setattr(route_module, "verify_token", lambda token: {"sub": "user"})

    async def _get_user(*args, **kwargs):
        return SimpleNamespace(google_refresh_token="refresh")

    monkeypatch.setattr(route_module.UserService, "get_user_by_google_id", _get_user)

    async def _refresh(refresh):
        return "access"

    async def _raise_reauth(*args, **kwargs):
        raise HTTPException(status_code=401, detail="google_reauth_required")

    monkeypatch.setattr(
        route_module.GoogleCalendarService, "refresh_access_token", _refresh
    )
    monkeypatch.setattr(
        route_module.GoogleCalendarService, "list_primary_events", _raise_reauth
    )

    response = asyncio.run(
        route_module.list_events(
            db=SimpleNamespace(),
            credentials=SimpleNamespace(scheme="Bearer", credentials="jwt"),
        )
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 401
    assert response.body == (
        b'{"code":"google_reauth_required","reauthUrl":"/user/google/login?force=1"}'
    )


def test_list_events_scope_missing_from_service(route_module, monkeypatch):
    monkeypatch.setattr(route_module, "verify_token", lambda token: {"sub": "user"})

    async def _get_user(*args, **kwargs):
        return SimpleNamespace(google_refresh_token="refresh")

    monkeypatch.setattr(route_module.UserService, "get_user_by_google_id", _get_user)

    async def _refresh(refresh):
        return "access"

    async def _raise_scope_missing(*args, **kwargs):
        raise HTTPException(status_code=400, detail="calendar_scope_missing")

    monkeypatch.setattr(
        route_module.GoogleCalendarService, "refresh_access_token", _refresh
    )
    monkeypatch.setattr(
        route_module.GoogleCalendarService, "list_primary_events", _raise_scope_missing
    )

    response = asyncio.run(
        route_module.list_events(
            db=SimpleNamespace(),
            credentials=SimpleNamespace(scheme="Bearer", credentials="jwt"),
        )
    )

    assert isinstance(response, JSONResponse)
    assert response.status_code == 400
    assert response.body == (
        b'{"code":"calendar_scope_missing","reauthUrl":"/user/google/login?force=1"}'
    )
