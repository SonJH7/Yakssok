from pydantic import BaseModel, Field
from typing import Optional


class EventDateTime(BaseModel):
    dateTime: str = Field(
        ..., description="RFC3339 format timestamp (e.g., 2026-01-15T10:00:00+09:00)"
    )
    timeZone: str = Field(default="Asia/Seoul", description="IANA timezone")


class Attendee(BaseModel):
    email: str


class EventCreateRequest(BaseModel):
    summary: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start: EventDateTime
    end: EventDateTime

    class Config:
        json_schema_extra = {
            "example": {
                "summary": "팀 미팅",
                "description": "주간 팀 미팅",
                "start": {
                    "dateTime": "2026-01-15T10:00:00+09:00",
                    "timeZone": "Asia/Seoul",
                },
                "end": {
                    "dateTime": "2026-01-15T11:00:00+09:00",
                    "timeZone": "Asia/Seoul",
                },
            }
        }


class EventCreateResponse(BaseModel):
    id: str
    summary: str
    htmlLink: str
    status: str
