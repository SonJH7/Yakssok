import importlib
import sys
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi import HTTPException


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    root_dir = Path(__file__).resolve().parents[2]
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")

    import app.variable

    importlib.reload(app.variable)


@pytest.fixture
def service_module():
    import app.services.google_calendar_service as module

    return importlib.reload(module)


class _FakeResponse:
    def __init__(self, status_code: int = 200, data: Dict[str, Any] | None = None):
        self.status_code = status_code
        self._data = data or {}
        self.ok = 200 <= status_code < 300

    def json(self) -> Dict[str, Any]:
        if self._data is None:
            raise ValueError("no json payload")
        return self._data


def test_refresh_access_token_success(service_module, monkeypatch):
    response = _FakeResponse(data={"access_token": "new-token"})
    monkeypatch.setattr(service_module.requests, "post", lambda *a, **k: response)

    token = service_module.GoogleCalendarService.refresh_access_token("refresh")

    assert token == "new-token"


def test_refresh_access_token_invalid_grant(service_module, monkeypatch):
    response = _FakeResponse(status_code=400, data={"error": "invalid_grant"})
    monkeypatch.setattr(service_module.requests, "post", lambda *a, **k: response)

    with pytest.raises(HTTPException) as exc:
        service_module.GoogleCalendarService.refresh_access_token("refresh")

    assert exc.value.status_code == 401
    assert exc.value.detail == "invalid_grant"


def test_refresh_access_token_server_error(service_module, monkeypatch):
    response = _FakeResponse(status_code=503, data={"error": "server_error"})
    monkeypatch.setattr(service_module.requests, "post", lambda *a, **k: response)

    with pytest.raises(HTTPException) as exc:
        service_module.GoogleCalendarService.refresh_access_token("refresh")

    assert exc.value.status_code == 500


def test_list_primary_events_success(service_module, monkeypatch):
    captured: Dict[str, Any] = {}

    def _fake_get(*args, **kwargs):
        captured.update(kwargs)
        return _FakeResponse(
            data={"items": [{"id": "1"}], "nextPageToken": "next-token"}
        )

    monkeypatch.setattr(service_module.requests, "get", _fake_get)

    result = service_module.GoogleCalendarService.list_primary_events(
        "access",
        time_min="2024-01-01T00:00:00Z",
        time_max="2024-01-31T23:59:59Z",
        max_results=10,
        page_token="page",
    )

    assert result == {"events": [{"id": "1"}], "nextPageToken": "next-token"}
    assert captured["headers"] == {"Authorization": "Bearer access"}
    assert captured["params"]["timeMin"] == "2024-01-01T00:00:00Z"
    assert captured["params"]["timeMax"] == "2024-01-31T23:59:59Z"
    assert captured["params"]["pageToken"] == "page"
    assert captured["params"]["maxResults"] == "10"


def test_list_primary_events_forbidden(service_module, monkeypatch):
    response = _FakeResponse(
        status_code=403, data={"error": {"message": "insufficient"}}
    )

    monkeypatch.setattr(service_module.requests, "get", lambda *a, **k: response)

    with pytest.raises(HTTPException) as exc:
        service_module.GoogleCalendarService.list_primary_events(
            "access", time_min=None, time_max=None
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "insufficient_scope"


def test_list_primary_events_requires_reauth(service_module, monkeypatch):
    response = _FakeResponse(status_code=401, data={"error": "invalid"})
    monkeypatch.setattr(service_module.requests, "get", lambda *a, **k: response)

    with pytest.raises(HTTPException) as exc:
        service_module.GoogleCalendarService.list_primary_events(
            "access", time_min=None, time_max=None
        )

    assert exc.value.status_code == 401
    assert exc.value.detail == "google_reauth_required"


def test_list_primary_events_rate_limited(service_module, monkeypatch):
    response = _FakeResponse(status_code=429, data={"error": {"message": "slow"}})
    monkeypatch.setattr(service_module.requests, "get", lambda *a, **k: response)

    with pytest.raises(HTTPException) as exc:
        service_module.GoogleCalendarService.list_primary_events(
            "access", time_min=None, time_max=None
        )

    assert exc.value.status_code == 429
    assert exc.value.detail == "rate_limited"
