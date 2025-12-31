import asyncio
import importlib
import inspect
import sys
from pathlib import Path
from typing import Any, Dict

import anyio
import pytest
from fastapi import HTTPException


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

            async def aclose(self):
                pass

        stub = types.SimpleNamespace(
            AsyncClient=_StubAsyncClient, RequestError=_StubRequestError
        )
        sys.modules["httpx"] = stub

    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")

    import app.variable

    importlib.reload(app.variable)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def service_module():
    import app.services.google_calendar_service as module

    reloaded = importlib.reload(module)
    reloaded.GoogleCalendarService._client = None
    reloaded.GoogleCalendarService._client_lock = None
    return reloaded


class _FakeResponse:
    def __init__(self, status_code: int = 200, data: Dict[str, Any] | None = None):
        self.status_code = status_code
        self._data = data or {}
        success = 200 <= status_code < 300
        self.ok = success
        self.is_success = success

    def json(self) -> Dict[str, Any]:
        if self._data is None:
            raise ValueError("no json payload")
        return self._data


class _FakeClient:
    def __init__(self, *, post=None, get=None):
        self._post = post
        self._get = get
        self.post_calls: list[Dict[str, Any]] = []
        self.get_calls: list[Dict[str, Any]] = []
        self.closed = False

    async def post(self, *args, **kwargs):
        self.post_calls.append({"args": args, "kwargs": kwargs})
        if self._post is None:
            raise AssertionError("post handler not configured")
        result = self._post(*args, **kwargs)
        if inspect.isawaitable(result):
            result = await result
        return result

    async def get(self, *args, **kwargs):
        self.get_calls.append({"args": args, "kwargs": kwargs})
        if self._get is None:
            raise AssertionError("get handler not configured")
        result = self._get(*args, **kwargs)
        if inspect.isawaitable(result):
            result = await result
        return result

    async def aclose(self):
        self.closed = True


def _override_client(monkeypatch, service_module, client):
    async def _get_client(cls):
        return client

    monkeypatch.setattr(
        service_module.GoogleCalendarService,
        "_get_client",
        classmethod(_get_client),
    )
    service_module.GoogleCalendarService._client = client


@pytest.mark.anyio
async def test_get_client_reuses_instance(service_module, monkeypatch):
    created = {}

    class _StubAsyncClient:
        def __init__(self, *args, **kwargs):
            created.setdefault("count", 0)
            created["count"] += 1
            created["kwargs"] = kwargs
            self.closed = False

        async def aclose(self):
            self.closed = True

    monkeypatch.setattr(service_module.httpx, "AsyncClient", _StubAsyncClient)

    client1 = await service_module.GoogleCalendarService._get_client()
    client2 = await service_module.GoogleCalendarService._get_client()

    assert client1 is client2
    assert created["count"] == 1
    assert created["kwargs"]["timeout"] == service_module.GoogleCalendarService._TIMEOUT

    await service_module.GoogleCalendarService.close_client()
    assert client1.closed is True
    assert service_module.GoogleCalendarService._client is None


@pytest.mark.anyio
async def test_client_lock_initialized_lazily(service_module, monkeypatch):
    assert service_module.GoogleCalendarService._client_lock is None

    class _StubAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def aclose(self):
            pass

    monkeypatch.setattr(service_module.httpx, "AsyncClient", _StubAsyncClient)

    await service_module.GoogleCalendarService._get_client()

    assert isinstance(service_module.GoogleCalendarService._client_lock, asyncio.Lock)

    await service_module.GoogleCalendarService.close_client()


@pytest.mark.anyio
async def test_close_client_resets_lock_for_new_event_loop(service_module, monkeypatch):
    created = {"count": 0}

    class _StubAsyncClient:
        def __init__(self, *args, **kwargs):
            created["count"] += 1

        async def aclose(self):
            pass

    monkeypatch.setattr(service_module.httpx, "AsyncClient", _StubAsyncClient)

    await service_module.GoogleCalendarService._get_client()
    await service_module.GoogleCalendarService.close_client()

    assert service_module.GoogleCalendarService._client is None
    assert service_module.GoogleCalendarService._client_lock is None

    async def _use_service_again():
        await service_module.GoogleCalendarService._get_client()
        await service_module.GoogleCalendarService.close_client()

    await anyio.to_thread.run_sync(lambda: asyncio.run(_use_service_again()))

    assert created["count"] == 2
    assert service_module.GoogleCalendarService._client is None
    assert service_module.GoogleCalendarService._client_lock is None


@pytest.mark.anyio
async def test_refresh_access_token_success(service_module, monkeypatch):
    response = _FakeResponse(data={"access_token": "new-token"})
    client = _FakeClient(post=lambda *args, **kwargs: response)
    _override_client(monkeypatch, service_module, client)

    token = await service_module.GoogleCalendarService.refresh_access_token("refresh")

    assert token == "new-token"
    assert (
        client.post_calls[0]["args"][0]
        == service_module.GoogleCalendarService.TOKEN_URL
    )


@pytest.mark.anyio
async def test_refresh_access_token_invalid_grant(service_module, monkeypatch):
    response = _FakeResponse(status_code=400, data={"error": "invalid_grant"})
    client = _FakeClient(post=lambda *args, **kwargs: response)
    _override_client(monkeypatch, service_module, client)

    with pytest.raises(HTTPException) as exc:
        await service_module.GoogleCalendarService.refresh_access_token("refresh")

    assert exc.value.status_code == 401
    assert exc.value.detail == "invalid_grant"


@pytest.mark.anyio
async def test_refresh_access_token_server_error(service_module, monkeypatch):
    response = _FakeResponse(status_code=503, data={"error": "server_error"})
    client = _FakeClient(post=lambda *args, **kwargs: response)
    _override_client(monkeypatch, service_module, client)

    with pytest.raises(HTTPException) as exc:
        await service_module.GoogleCalendarService.refresh_access_token("refresh")

    assert exc.value.status_code == 500


@pytest.mark.anyio
async def test_list_primary_events_success(service_module, monkeypatch):
    response = _FakeResponse(
        data={"items": [{"id": "1"}], "nextPageToken": "next-token"}
    )
    client = _FakeClient(get=lambda *args, **kwargs: response)
    _override_client(monkeypatch, service_module, client)

    result = await service_module.GoogleCalendarService.list_primary_events(
        "access",
        time_min="2024-01-01T00:00:00Z",
        time_max="2024-01-31T23:59:59Z",
        max_results=10,
        page_token="page",
    )

    assert result == {"events": [{"id": "1"}], "nextPageToken": "next-token"}
    call = client.get_calls[0]
    params = call["kwargs"]["params"]
    assert params["timeMin"] == "2024-01-01T00:00:00Z"
    assert params["timeMax"] == "2024-01-31T23:59:59Z"
    assert params["pageToken"] == "page"
    assert params["maxResults"] == "10"
    assert (
        params["fields"]
        == "items(id,status,summary,description,location,start,end,htmlLink,"
        "organizer,creator,attendees,updated),nextPageToken"
    )


@pytest.mark.anyio
async def test_list_primary_events_forbidden(service_module, monkeypatch):
    response = _FakeResponse(
        status_code=403,
        data={"error": {"errors": [{"reason": "insufficientPermissions"}]}},
    )
    client = _FakeClient(get=lambda *args, **kwargs: response)
    _override_client(monkeypatch, service_module, client)

    with pytest.raises(HTTPException) as exc:
        await service_module.GoogleCalendarService.list_primary_events(
            "access", time_min=None, time_max=None
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "insufficient_scope"


@pytest.mark.anyio
async def test_list_primary_events_requires_reauth(service_module, monkeypatch):
    response = _FakeResponse(status_code=401, data={"error": "invalid"})
    client = _FakeClient(get=lambda *args, **kwargs: response)
    _override_client(monkeypatch, service_module, client)

    with pytest.raises(HTTPException) as exc:
        await service_module.GoogleCalendarService.list_primary_events(
            "access", time_min=None, time_max=None
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "google_reauth_required"


@pytest.mark.anyio
async def test_list_primary_events_rate_limited(service_module, monkeypatch):
    response = _FakeResponse(status_code=429, data={"error": {"message": "slow"}})
    client = _FakeClient(get=lambda *args, **kwargs: response)
    _override_client(monkeypatch, service_module, client)

    with pytest.raises(HTTPException) as exc:
        await service_module.GoogleCalendarService.list_primary_events(
            "access", time_min=None, time_max=None
        )

    assert exc.value.status_code == 429
    assert exc.value.detail == "rate_limited"


@pytest.mark.anyio
async def test_list_primary_events_scope_missing_from_google_message(
    service_module, monkeypatch
):
    response = _FakeResponse(
        status_code=400,
        data={
            "error": {
                "message": "Calendar access denied",
                "errors": [
                    {
                        "message": "CalendarAccessDenied",
                        "reason": "calendarAccessDenied",
                    }
                ],
            }
        },
    )
    client = _FakeClient(get=lambda *args, **kwargs: response)
    _override_client(monkeypatch, service_module, client)

    with pytest.raises(HTTPException) as exc:
        await service_module.GoogleCalendarService.list_primary_events(
            "access", time_min=None, time_max=None
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "calendar_scope_missing"
