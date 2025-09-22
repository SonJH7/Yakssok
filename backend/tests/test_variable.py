import importlib
import sys
from pathlib import Path


def test_frontend_url_default(monkeypatch):
    root_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root_dir))
    monkeypatch.delenv("FRONTEND_URL", raising=False)
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_MINUTES", "120")
    monkeypatch.setenv("SECRET_KEY", "test")
    monkeypatch.setenv("ALGORITHM", "HS256")
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URL_USER", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost")
    module = importlib.import_module("app.variable")
    reloaded = importlib.reload(module)

    assert reloaded.FRONTEND_URL == "localhost:5173"
