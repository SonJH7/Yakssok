import asyncio
import importlib
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


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
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost")
    import app.variable  # noqa: F401

    importlib.reload(app.variable)


class FakeAsyncSession:
    def __init__(self, session: Session, engine):
        self._session = session
        self._engine = engine

    def add(self, obj):
        self._session.add(obj)

    async def commit(self):
        self._session.commit()

    async def refresh(self, obj):
        self._session.refresh(obj)

    async def execute(self, statement):
        return self._session.execute(statement)

    async def close(self):
        self._session.close()
        self._engine.dispose()


@pytest.fixture()
def session_factory():
    from app.db.base import Base

    @asynccontextmanager
    async def factory():
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        fake_session = FakeAsyncSession(session, engine)
        try:
            yield fake_session
        finally:
            await fake_session.close()

    return factory


def test_create_and_get_user(session_factory):
    from app.services.user_service import UserService

    async def scenario():
        async with session_factory() as session:
            user = await UserService.create_user(
                "gid", "user@example.com", "User", "refresh", session
            )
            fetched = await UserService.get_user_by_google_id("gid", session)
            return user, fetched

    user, fetched = asyncio.run(scenario())

    assert fetched is not None
    assert fetched.user_id == "gid"
    assert user.email == "user@example.com"


def test_update_refresh_token(session_factory):
    from app.services.user_service import UserService

    async def scenario():
        async with session_factory() as session:
            user = await UserService.create_user(
                "gid", "user@example.com", "User", "refresh", session
            )
            await UserService.update_refresh_token(user, "new-refresh", session)
            await session.refresh(user)
            return user.google_refresh_token

    updated_token = asyncio.run(scenario())

    assert updated_token == "new-refresh"


def test_get_or_create_user_creates_new(session_factory):
    from app.services.user_service import UserService

    async def scenario():
        async with session_factory() as session:
            user = await UserService.get_or_create_user(
                "gid", "user@example.com", "User", "refresh", session
            )
            return user

    user = asyncio.run(scenario())

    assert user.user_id == "gid"


def test_get_or_create_user_updates_existing(session_factory):
    from app.services.user_service import UserService

    async def scenario():
        async with session_factory() as session:
            user = await UserService.create_user(
                "gid", "user@example.com", "User", "refresh", session
            )
            await UserService.get_or_create_user(
                "gid", "user@example.com", "User", "new-refresh", session
            )
            await session.refresh(user)
            return user.google_refresh_token

    token = asyncio.run(scenario())

    assert token == "new-refresh"
