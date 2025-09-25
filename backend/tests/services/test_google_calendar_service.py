import importlib
import sys
from pathlib import Path

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
def service_module(monkeypatch):
    import app.services.google_calendar_service as module

    module = importlib.reload(module)

    yield module


class _FakeResponse:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data or {}
        self.ok = 200 <= status_code < 300

    def json(self):
        if self._data is None:
            raise ValueError("no json")
        return self._data


def test_refresh_access_token_success(service_module, monkeypatch):
    response = _FakeResponse(data={"access_token": "new-token"})
    monkeypatch.setattr(service_module.requests, "post", lambda *a, **k: response)

    token = service_module.GoogleCalendarService.refresh_access_token("refresh")

    assert token == "new-token"


@pytest.mark.parametrize(
    "status_code,data,expected_status",
    [
        (400, {"error": "invalid_grant"}, 401),
        (500, {"error": "server_error"}, 500),
    ],
)
def test_refresh_access_token_failure(
    service_module, monkeypatch, status_code, data, expected_status
):
    response = _FakeResponse(status_code=status_code, data=data)
    monkeypatch.setattr(service_module.requests, "post", lambda *a, **k: response)

    with pytest.raises(HTTPException) as exc:
        service_module.GoogleCalendarService.refresh_access_token("refresh")

    assert exc.value.status_code == expected_status


def test_list_primary_events_success(service_module, monkeypatch):
    payload = {"items": [{"id": "1"}], "nextPageToken": "token"}
    response = _FakeResponse(data=payload)
    monkeypatch.setattr(service_module.requests, "get", lambda *a, **k: response)

    result = service_module.GoogleCalendarService.list_primary_events(
        "access",
        time_min="2024-01-01T00:00:00Z",
        time_max="2024-01-31T23:59:59Z",
        max_results=10,
        page_token="next",
    )

    assert result == {"events": payload["items"], "nextPageToken": "token"}


@pytest.mark.parametrize(
    "status_code,expected_status",
    [
        (403, 403),
        (429, 429),
        (500, 500),
    ],
)
def test_list_primary_events_errors(
    service_module, monkeypatch, status_code, expected_status
):
    data = {"error": {"message": "nope"}}
    response = _FakeResponse(status_code=status_code, data=data)
    monkeypatch.setattr(service_module.requests, "get", lambda *a, **k: response)

    with pytest.raises(HTTPException) as exc:
        service_module.GoogleCalendarService.list_primary_events(
            "access",
            time_min=None,
            time_max=None,
        )

    assert exc.value.status_code == expected_status
