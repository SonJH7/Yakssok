from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schema.calendar_schema import EventCreateRequest, EventCreateResponse
from app.services.google_calendar_service import GoogleCalendarService
from app.services.user_service import UserService
from app.utils.jwt import verify_token

security = HTTPBearer(auto_error=False)

router = APIRouter(prefix="/calendar")

REAUTH_URL = "/user/google/login?force=1"


@router.get("/events")
async def list_events(
    time_min: str | None = None,
    time_max: str | None = None,
    max_results: int = 50,
    page_token: str | None = None,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")

    payload = verify_token(credentials.credentials)
    user_id = payload.get("sub") if payload else None
    if not user_id:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    user = await UserService.get_user_by_google_id(user_id, db)
    if not user or not getattr(user, "google_refresh_token", None):
        return JSONResponse(
            status_code=400,
            content={
                "code": "calendar_scope_missing",
                "reauthUrl": REAUTH_URL,
            },
        )

    try:
        access_token = await GoogleCalendarService.refresh_access_token(
            user.google_refresh_token
        )
    except HTTPException as exc:
        if exc.status_code == 401:
            return JSONResponse(
                status_code=401,
                content={
                    "code": "google_reauth_required",
                    "reauthUrl": REAUTH_URL,
                },
            )
        raise

    try:
        events_payload = await GoogleCalendarService.list_primary_events(
            access_token,
            time_min=time_min,
            time_max=time_max,
            max_results=max_results,
            page_token=page_token,
        )
    except HTTPException as exc:
        if exc.status_code == 401:
            return JSONResponse(
                status_code=401,
                content={
                    "code": "google_reauth_required",
                    "reauthUrl": REAUTH_URL,
                },
            )
        if exc.status_code == 400 and exc.detail == "calendar_scope_missing":
            return JSONResponse(
                status_code=400,
                content={
                    "code": "calendar_scope_missing",
                    "reauthUrl": REAUTH_URL,
                },
            )
        if exc.status_code == 403:
            return JSONResponse(
                status_code=403,
                content={
                    "code": "insufficient_scope",
                    "reauthUrl": REAUTH_URL,
                },
            )
        raise

    return events_payload


@router.post("/events", response_model=EventCreateResponse)
async def add_events(
    event_request: EventCreateRequest,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")

    payload = verify_token(credentials.credentials)
    user_id = payload.get("sub") if payload else None
    if not user_id:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    user = await UserService.get_user_by_google_id(user_id, db)
    if not user or not getattr(user, "google_refresh_token", None):
        return JSONResponse(
            status_code=400,
            content={
                "code": "calendar_scope_missing",
                "reauthUrl": REAUTH_URL,
            },
        )

    try:
        access_token = await GoogleCalendarService.refresh_access_token(
            user.google_refresh_token
        )
    except HTTPException as exc:
        if exc.status_code == 401:
            return JSONResponse(
                status_code=401,
                content={
                    "code": "google_reauth_required",
                    "reauthUrl": REAUTH_URL,
                },
            )
        raise

    event_data = event_request.model_dump(exclude_none=True)

    try:
        created_event = await GoogleCalendarService.create_event(
            access_token,
            event_data,
        )
    except HTTPException as exc:
        if exc.status_code == 401:
            return JSONResponse(
                status_code=401,
                content={
                    "code": "google_reauth_required",
                    "reauthUrl": REAUTH_URL,
                },
            )
        if exc.status_code == 400 and exc.detail == "calendar_scope_missing":
            return JSONResponse(
                status_code=400,
                content={
                    "code": "calendar_scope_missing",
                    "reauthUrl": REAUTH_URL,
                },
            )
        if exc.status_code == 403:
            return JSONResponse(
                status_code=403,
                content={
                    "code": "insufficient_scope",
                    "reauthUrl": REAUTH_URL,
                },
            )
        raise

    return created_event


@router.delete("/events/{event_id}")
async def delete_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")

    payload = verify_token(credentials.credentials)
    user_id = payload.get("sub") if payload else None
    if not user_id:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    user = await UserService.get_user_by_google_id(user_id, db)
    if not user or not getattr(user, "google_refresh_token", None):
        return JSONResponse(
            status_code=400,
            content={
                "code": "calendar_scope_missing",
                "reauthUrl": REAUTH_URL,
            },
        )

    try:
        access_token = await GoogleCalendarService.refresh_access_token(
            user.google_refresh_token
        )
    except HTTPException as exc:
        if exc.status_code == 401:
            return JSONResponse(
                status_code=401,
                content={
                    "code": "google_reauth_required",
                    "reauthUrl": REAUTH_URL,
                },
            )
        raise

    try:
        deleted_event = await GoogleCalendarService.delete_event(
            access_token,
            event_id,
        )
    except HTTPException as exc:
        if exc.status_code == 401:
            return JSONResponse(
                status_code=401,
                content={
                    "code": "google_reauth_required",
                    "reauthUrl": REAUTH_URL,
                },
            )
        if exc.status_code == 400 and exc.detail == "calendar_scope_missing":
            return JSONResponse(
                status_code=400,
                content={
                    "code": "calendar_scope_missing",
                    "reauthUrl": REAUTH_URL,
                },
            )
        if exc.status_code == 403:
            return JSONResponse(
                status_code=403,
                content={
                    "code": "insufficient_scope",
                    "reauthUrl": REAUTH_URL,
                },
            )
        if exc.status_code == 404:
            return JSONResponse(
                status_code=404,
                content={
                    "code": "event_not_found",
                },
            )
        raise

    return deleted_event
