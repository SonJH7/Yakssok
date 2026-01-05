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


class SyncMySchedulesResponse(BaseModel):
    total_appointments: int
    updated_count: int
    failed_count: int


class ConfirmAppointmentRequest(BaseModel):
    confirmed_date: date
    confirmed_start_time: str
    confirmed_end_time: str

    @validator("confirmed_start_time", "confirmed_end_time")
    def validate_time_format(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("시간 형식은 HH:MM이어야 합니다 (예: 09:00)")
        return v


class ConfirmAppointmentResponse(BaseModel):
    id: int
    name: str
    status: str
    confirmed_date: Optional[date]
    confirmed_start_time: Optional[str]
    confirmed_end_time: Optional[str]
    confirmed_at: Optional[datetime]

    class Config:
        from_attributes = True
