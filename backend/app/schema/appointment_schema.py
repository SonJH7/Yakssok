from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import date, datetime
import json


class AppointmentCreateRequest(BaseModel):
    name: str
    candidate_dates: List[date]
    max_participants: int


class AppointmentResponse(BaseModel):
    id: int
    name: str
    creator_id: int
    max_participants: int
    status: str
    invite_link: str
    candidate_dates: List[date]

    class Config:
        from_attributes = True


class AppointmentDateResponse(BaseModel):
    id: int
    appointment_id: int
    candidate_date: date

    class Config:
        from_attributes = True


class JoinAppointmentRequest(BaseModel):
    invite_code: str


class AvailableTimeRange(BaseModel):
    start: str
    end: str


class AvailableDateSlot(BaseModel):
    date: date
    available_times: List[AvailableTimeRange]


class AvailableSlotsData(BaseModel):
    timezone: str
    slots: List[AvailableDateSlot]
    calculated_at: datetime


class ParticipationResponse(BaseModel):
    id: int
    user_id: int
    appointment_id: int
    status: str
    available_slots: Optional[AvailableSlotsData] = None

    @validator("available_slots", pre=True)
    def parse_available_slots(cls, v):
        if v and isinstance(v, str):
            return json.loads(v)
        return v

    class Config:
        from_attributes = True


class OptimalTimeSlot(BaseModel):
    date: date
    start_time: str
    end_time: str
    duration_minutes: int
    participant_count: int
    total_participants: int
    participant_ids: List[int]
    availability_percentage: float


class OptimalTimesResponse(BaseModel):
    appointment_id: int
    appointment_name: str
    total_participants: int
    optimal_times: List[OptimalTimeSlot]
    calculation_status: str


class DateAvailability(BaseModel):
    date: date
    availability: str
    available_count: int
    total_count: int


class AppointmentDetailResponse(BaseModel):
    id: int
    name: str
    creator_id: str
    max_participants: int
    status: str
    invite_link: str
    total_participants: int
    participants_with_data: int
    dates: List[DateAvailability]


class AppointmentListResponse(BaseModel):
    id: int
    name: str
    invite_link: str

    class Config:
        from_attributes = True
