import importlib
import sys
from pathlib import Path


_ROOT_DIR = Path(__file__).resolve().parents[1]
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))


_COMMON_ENV = {
    "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    "REFRESH_TOKEN_EXPIRE_MINUTES": "120",
    "SECRET_KEY": "test",
    "ALGORITHM": "HS256",
    "SQLALCHEMY_DATABASE_URL_USER": "sqlite+aiosqlite:///:memory:",
    "GOOGLE_CLIENT_ID": "client",
    "GOOGLE_CLIENT_SECRET": "secret",
    "GOOGLE_REDIRECT_URI": "http://localhost",
}

_UNSET = object()


def _reload_variable(monkeypatch, frontend_url=_UNSET):
    for key, value in _COMMON_ENV.items():
        monkeypatch.setenv(key, value)

    if frontend_url is _UNSET:
        monkeypatch.delenv("FRONTEND_URL", raising=False)
    elif frontend_url is None:
        monkeypatch.delenv("FRONTEND_URL", raising=False)
    else:
        monkeypatch.setenv("FRONTEND_URL", frontend_url)

    module = importlib.import_module("app.variable")

    return importlib.reload(module)


def test_frontend_url_default(monkeypatch):
    reloaded = _reload_variable(monkeypatch)

    assert reloaded.FRONTEND_URL == "http://localhost:5173"


def test_frontend_url_without_scheme(monkeypatch):
    reloaded = _reload_variable(monkeypatch, "example.com")

    assert reloaded.FRONTEND_URL == "http://example.com"


def test_frontend_url_without_scheme_but_with_port(monkeypatch):
    reloaded = _reload_variable(monkeypatch, "localhost:5173")

    assert reloaded.FRONTEND_URL == "http://localhost:5173"


def test_frontend_url_with_path(monkeypatch):
    reloaded = _reload_variable(monkeypatch, "example.com/app")

    assert reloaded.FRONTEND_URL == "http://example.com/app"


def test_frontend_url_strips_whitespace(monkeypatch):
    reloaded = _reload_variable(monkeypatch, "  example.com \n")

    assert reloaded.FRONTEND_URL == "http://example.com"


def test_frontend_url_preserves_valid_scheme(monkeypatch):
    reloaded = _reload_variable(monkeypatch, "https://app.example.com")

    assert reloaded.FRONTEND_URL == "https://app.example.com"


def test_frontend_url_handles_network_path_reference(monkeypatch):
    reloaded = _reload_variable(monkeypatch, "//localhost:5173")

    assert reloaded.FRONTEND_URL == "http://localhost:5173"


def test_frontend_url_ignores_unknown_scheme(monkeypatch):
    reloaded = _reload_variable(monkeypatch, "custom://localhost:5173")

    assert reloaded.FRONTEND_URL == "http://localhost:5173"
