from pydantic import BaseModel, Field, model_validator
from typing import Optional


class EventDateTime(BaseModel):
    dateTime: str = Field(
        ..., description="RFC3339 format timestamp (e.g., 2026-01-15T10:00:00+09:00)"
    )
    timeZone: str = Field(default="Asia/Seoul", description="IANA timezone")


class EventDateInput(BaseModel):
    date: Optional[str] = Field(None, description="All-day date (YYYY-MM-DD)")
    dateTime: Optional[str] = Field(
        None, description="RFC3339 format timestamp (e.g., 2026-01-15T10:00:00+09:00)"
    )
    timeZone: Optional[str] = Field(None, description="IANA timezone")

    @model_validator(mode="after")
    def validate_date_or_datetime(self):
        if self.date and self.dateTime:
            raise ValueError("Provide either date or dateTime, not both.")
        if not self.date and not self.dateTime:
            raise ValueError("Either date or dateTime is required.")
        return self


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


class EventUpdateRequest(BaseModel):
    summary: Optional[str] = Field(None, description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start: Optional[EventDateInput] = Field(None, description="Event start time")
    end: Optional[EventDateInput] = Field(None, description="Event end time")

    @model_validator(mode="after")
    def validate_start_end_type(self):
        if self.start and self.end:
            if bool(self.start.date) != bool(self.end.date):
                raise ValueError(
                    "start and end must use the same type (date or dateTime)."
                )
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "summary": "Updated meeting title",
                "description": "Updated meeting description",
                "start": {
                    "dateTime": "2026-01-15T11:00:00+09:00",
                    "timeZone": "Asia/Seoul",
                },
                "end": {
                    "dateTime": "2026-01-15T12:00:00+09:00",
                    "timeZone": "Asia/Seoul",
                },
            }
        }


class EventCreateResponse(BaseModel):
    id: str
    summary: str
    htmlLink: str
    status: str
