from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional, Set

import httpx
from fastapi import HTTPException

from app.variable import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

LOGGER = logging.getLogger(__name__)


class GoogleCalendarService:
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    _TIMEOUT = 10
    _client: httpx.AsyncClient | None = None
    _client_lock: asyncio.Lock | None = None

    @classmethod
    def _ensure_lock(cls) -> asyncio.Lock:
        lock = cls._client_lock
        if lock is None:
            lock = asyncio.Lock()
            cls._client_lock = lock
        return lock

    @classmethod
    async def _get_client(cls) -> httpx.AsyncClient:
        if cls._client is None:
            async with cls._ensure_lock():
                if cls._client is None:
                    cls._client = httpx.AsyncClient(timeout=cls._TIMEOUT)
        return cls._client

    @classmethod
    async def close_client(cls) -> None:
        client: httpx.AsyncClient | None = None
        lock = cls._client_lock
        if lock is not None:
            async with lock:
                client = cls._client
                cls._client = None
        else:
            client = cls._client
            cls._client = None

        cls._client_lock = None

        if client is not None:
            await client.aclose()

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> str:
        payload = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        client = await cls._get_client()

        try:
            response = await client.post(cls.TOKEN_URL, data=payload)
        except httpx.RequestError as exc:  # pragma: no cover - network guard
            LOGGER.exception("Failed to refresh Google access token: %s", exc)
            raise HTTPException(
                status_code=500, detail="구글 토큰 갱신 요청에 실패했습니다."
            ) from exc

        data: Dict[str, Any] = cls._safe_json(response)
        if response.is_success and data.get("access_token"):
            return data["access_token"]

        error = data.get("error")
        description = data.get("error_description")
        LOGGER.error(
            "Google token refresh failed (status=%s, error=%s, description=%s)",
            response.status_code,
            error,
            description,
        )

        if response.status_code == 400 and error == "invalid_grant":
            raise HTTPException(status_code=401, detail="invalid_grant")

        raise HTTPException(status_code=500, detail="구글 토큰 갱신에 실패했습니다.")

    @classmethod
    async def list_primary_events(
        cls,
        access_token: str,
        *,
        time_min: Optional[str],
        time_max: Optional[str],
        max_results: int = 50,
        page_token: Optional[str] = None,
        time_zone: str = "Asia/Seoul",
    ) -> Dict[str, Any]:
        params: Dict[str, str] = {
            "singleEvents": "true",
            "orderBy": "startTime",
            "timeZone": time_zone,
            "maxResults": str(max_results),
            "fields": (
                "items("
                "id,status,summary,description,location,start,end,htmlLink,"
                "organizer,creator,attendees,updated"
                "),nextPageToken"
            ),
        }
        if time_min is not None:
            params["timeMin"] = time_min
        if time_max is not None:
            params["timeMax"] = time_max
        if page_token is not None:
            params["pageToken"] = page_token

        headers = {"Authorization": f"Bearer {access_token}"}

        client = await cls._get_client()

        try:
            response = await client.get(cls.EVENTS_URL, headers=headers, params=params)
        except httpx.RequestError as exc:  # pragma: no cover - network guard
            LOGGER.exception("Failed to fetch Google Calendar events: %s", exc)
            raise HTTPException(
                status_code=500, detail="구글 캘린더 이벤트 조회에 실패했습니다."
            ) from exc

        data: Dict[str, Any] = cls._safe_json(response)
        if response.is_success:
            return {
                "events": data.get("items", []),
                "nextPageToken": data.get("nextPageToken"),
            }

        error_info = cls._extract_calendar_error(data)
        error_tokens = cls._extract_calendar_error_tokens(data)
        LOGGER.error(
            "Google Calendar API error (status=%s, error=%s)",
            response.status_code,
            error_info,
        )

        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="google_reauth_required")
        if response.status_code == 429:
            raise HTTPException(status_code=429, detail="rate_limited")

        if cls._matches_scope_missing(error_tokens):
            raise HTTPException(status_code=400, detail="calendar_scope_missing")

        if response.status_code == 403 or cls._matches_insufficient_scope(error_tokens):
            raise HTTPException(status_code=403, detail="insufficient_scope")

        raise HTTPException(status_code=500, detail="구글 캘린더 조회에 실패했습니다.")

    @staticmethod
    def _safe_json(response: Any) -> Dict[str, Any]:
        try:
            return response.json()
        except ValueError:  # pragma: no cover - unexpected payload
            return {}

    @staticmethod
    def _extract_calendar_error(data: Dict[str, Any]) -> Optional[str]:
        error = data.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str):
                return message
            errors = error.get("errors")
            if isinstance(errors, list):
                for entry in errors:
                    if isinstance(entry, dict):
                        message = entry.get("message")
                        if isinstance(message, str):
                            return message
                        reason = entry.get("reason")
                        if isinstance(reason, str):
                            return reason
        if isinstance(error, str):
            return error
        return None

    @classmethod
    def _extract_calendar_error_tokens(cls, data: Dict[str, Any]) -> Set[str]:
        tokens: Set[str] = set()
        error = data.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str):
                tokens.add(cls._normalize_error_token(message))
            errors = error.get("errors")
            if isinstance(errors, list):
                for entry in errors:
                    if isinstance(entry, dict):
                        for key in ("reason", "message"):
                            value = entry.get(key)
                            if isinstance(value, str):
                                tokens.add(cls._normalize_error_token(value))
        elif isinstance(error, str):
            tokens.add(cls._normalize_error_token(error))
        return {token for token in tokens if token}

    @staticmethod
    def _normalize_error_token(value: str) -> str:
        return value.replace("-", "_").replace(" ", "_").lower()

    @classmethod
    def _matches_scope_missing(cls, tokens: Set[str]) -> bool:
        scope_missing_errors = {
            "calendaraccessdenied",
            "calendar_access_denied",
            "accessnotconfigured",
        }
        return any(token in scope_missing_errors for token in tokens)

    @classmethod
    def _matches_insufficient_scope(cls, tokens: Set[str]) -> bool:
        insufficient_scope_errors = {
            "insufficientpermissions",
            "insufficient_scope",
        }
        return any(token in insufficient_scope_errors for token in tokens)
