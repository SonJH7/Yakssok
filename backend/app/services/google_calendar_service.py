from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests
from fastapi import HTTPException

from app.variable import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

LOGGER = logging.getLogger(__name__)


class GoogleCalendarService:
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

    @classmethod
    def refresh_access_token(cls, refresh_token: str) -> str:
        payload = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        try:
            response = requests.post(cls.TOKEN_URL, data=payload, timeout=10)
        except requests.RequestException as exc:  # pragma: no cover - network guard
            LOGGER.exception("Failed to refresh Google access token: %s", exc)
            raise HTTPException(
                status_code=500, detail="구글 토큰 갱신 요청에 실패했습니다."
            ) from exc

        data: Dict[str, Any] = cls._safe_json(response)
        if response.ok and data.get("access_token"):
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
    def list_primary_events(
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
            "fields": "items(id,summary,location,start,end,htmlLink,updated),nextPageToken",
        }
        if time_min is not None:
            params["timeMin"] = time_min
        if time_max is not None:
            params["timeMax"] = time_max
        if page_token is not None:
            params["pageToken"] = page_token

        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = requests.get(
                cls.EVENTS_URL, headers=headers, params=params, timeout=10
            )
        except requests.RequestException as exc:  # pragma: no cover - network guard
            LOGGER.exception("Failed to fetch Google Calendar events: %s", exc)
            raise HTTPException(
                status_code=500, detail="구글 캘린더 이벤트 조회에 실패했습니다."
            ) from exc

        data: Dict[str, Any] = cls._safe_json(response)
        if response.ok:
            return {
                "events": data.get("items", []),
                "nextPageToken": data.get("nextPageToken"),
            }

        error_info = cls._extract_calendar_error(data)
        LOGGER.error(
            "Google Calendar API error (status=%s, error=%s)",
            response.status_code,
            error_info,
        )
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="google_reauth_required")
        if response.status_code == 403:
            raise HTTPException(status_code=403, detail="insufficient_scope")
        if response.status_code == 429:
            raise HTTPException(status_code=429, detail="rate_limited")

        raise HTTPException(status_code=500, detail="구글 캘린더 조회에 실패했습니다.")

    @staticmethod
    def _safe_json(response: requests.Response) -> Dict[str, Any]:
        try:
            return response.json()
        except ValueError:  # pragma: no cover - unexpected payload
            return {}

    @staticmethod
    def _extract_calendar_error(data: Dict[str, Any]) -> Optional[str]:
        error = data.get("error")
        if isinstance(error, dict):
            return error.get("message")
        if isinstance(error, str):
            return error
        return None
