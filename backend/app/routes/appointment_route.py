from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.db.session import get_db
from app.models.appointment_model import Participations
from app.services.appointment_service import AppointmentService
from app.schema.appointment_schema import (
    AppointmentCreateRequest,
    AppointmentResponse,
    JoinAppointmentRequest,
    ParticipationResponse,
    OptimalTimesResponse,
    AppointmentDetailResponse,
    AppointmentListResponse,
    SyncMySchedulesResponse,
    ConfirmAppointmentRequest,
    ConfirmAppointmentResponse,
)
from app.utils.jwt import get_current_user

security = HTTPBearer()

router = APIRouter(
    prefix="/appointments",
)


@router.post("/", response_model=AppointmentResponse)
async def create_appointment(
    request: AppointmentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # 약속 생성
    try:
        appointment = await AppointmentService.create_appointment(
            request=request, creator_id=current_user["sub"], db=db
        )

        appointment_dates = await AppointmentService.get_appointment_dates(
            appointment.id, db
        )

        return AppointmentResponse(
            id=appointment.id,
            name=appointment.name,
            creator_id=appointment.creator_id,
            max_participants=appointment.max_participants,
            status=appointment.status,
            invite_link=appointment.invite_link,
            candidate_dates=[ad.candidate_date for ad in appointment_dates],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"약속 생성 실패: {str(e)}")


@router.get("/", response_model=list[AppointmentListResponse])
async def get_my_appointments(
    db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    # 내 약속 목록 조회
    try:
        appointments = await AppointmentService.get_my_appointments(
            user_id=current_user["sub"], db=db
        )

        return [
            AppointmentListResponse(
                id=appointment.id,
                name=appointment.name,
                invite_link=appointment.invite_link,
            )
            for appointment in appointments
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"약속 목록 조회 실패: {str(e)}")


@router.get("/{invite_code}", response_model=AppointmentResponse)
async def get_appointment_by_invite_code(
    invite_code: str, db: AsyncSession = Depends(get_db)
):
    # 초대 코드로 약속 조회
    appointment = await AppointmentService.get_appointment_by_invite_code(
        invite_code, db
    )

    if not appointment:
        raise HTTPException(status_code=404, detail="존재하지 않는 약속입니다")

    appointment_dates = await AppointmentService.get_appointment_dates(
        appointment.id, db
    )

    return AppointmentResponse(
        id=appointment.id,
        name=appointment.name,
        creator_id=appointment.creator_id,
        max_participants=appointment.max_participants,
        status=appointment.status,
        invite_link=appointment.invite_link,
        candidate_dates=[ad.candidate_date for ad in appointment_dates],
    )


@router.get("/{invite_code}/detail", response_model=AppointmentDetailResponse)
async def get_appointment_detail(invite_code: str, db: AsyncSession = Depends(get_db)):
    # 약쇽 세부 조회
    try:
        detail = await AppointmentService.get_appointment_detail_with_availability(
            invite_code, db
        )
        return detail
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"약속 조회 실패: {str(e)}")


@router.post("/join", response_model=ParticipationResponse)
async def join_appointment(
    request: JoinAppointmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # 초대 코드로 약속 참여
    try:
        participation = await AppointmentService.join_appointment(
            invite_code=request.invite_code, user_id=current_user["sub"], db=db
        )

        return ParticipationResponse(
            id=participation.id,
            user_id=participation.user_id,
            appointment_id=participation.appointment_id,
            status=participation.status,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"약속 참여 실패: {str(e)}")


@router.delete("/{invite_code}")
async def delete_appointment(
    invite_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # 약속 삭제
    try:
        await AppointmentService.delete_appointment(
            invite_code=invite_code, user_id=current_user["sub"], db=db
        )
        return {"message": "약속이 삭제되었습니다"}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"약속 삭제 실패: {str(e)}")


@router.get("/{invite_code}/optimal-times", response_model=OptimalTimesResponse)
async def get_optimal_times(
    invite_code: str,
    min_duration_minutes: int = 60,
    time_range_start: str = None,
    time_range_end: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # 약속 조회
    appointment = await AppointmentService.get_appointment_by_invite_code(
        invite_code, db
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="약속을 찾을 수 없습니다")

    participation = await AppointmentService._get_participation(
        current_user["sub"], appointment.id, db
    )
    if not participation:
        raise HTTPException(status_code=403, detail="참여자만 조회할 수 있습니다")

    # 최적 시간 계산
    optimal_times = await AppointmentService.calculate_optimal_times(
        appointment.id,
        min_duration_minutes,
        db,
        time_range_start=time_range_start,
        time_range_end=time_range_end,
    )

    # 전체 참여자 수
    total_result = await db.execute(
        select(func.count(Participations.id)).where(
            Participations.appointment_id == appointment.id
        )
    )
    total_participants = total_result.scalar()

    # 가용시간 제공한 참여자 수
    available_result = await db.execute(
        select(func.count(Participations.id))
        .where(Participations.appointment_id == appointment.id)
        .where(Participations.available_slots.isnot(None))
    )
    participants_with_data = available_result.scalar()

    # 상태 결정
    if participants_with_data == 0:
        calculation_status = "no_data"
    elif participants_with_data < total_participants:
        calculation_status = "partial"
    else:
        calculation_status = "complete"

    return OptimalTimesResponse(
        appointment_id=appointment.id,
        appointment_name=appointment.name,
        total_participants=total_participants,
        optimal_times=optimal_times,
        calculation_status=calculation_status,
    )


@router.post("/sync-my-schedules", response_model=SyncMySchedulesResponse)
async def sync_my_schedules(
    db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    # 내가 참여한 모든 약속의 일정 동기화
    try:
        result = await AppointmentService.sync_my_schedules(
            user_id=current_user["sub"], db=db
        )

        return SyncMySchedulesResponse(
            total_appointments=result["total_appointments"],
            updated_count=result["updated_count"],
            failed_count=result["failed_count"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일정 동기화 실패: {str(e)}")


@router.post("/{invite_code}/confirm", response_model=ConfirmAppointmentResponse)
async def confirm_appointment(
    invite_code: str,
    request: ConfirmAppointmentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # 약속 확정
    try:
        appointment = await AppointmentService.confirm_appointment(
            invite_code=invite_code,
            confirmed_date=request.confirmed_date,
            confirmed_start_time=request.confirmed_start_time,
            confirmed_end_time=request.confirmed_end_time,
            user_id=current_user["sub"],
            db=db,
        )

        return ConfirmAppointmentResponse(
            id=appointment.id,
            name=appointment.name,
            status=appointment.status,
            confirmed_date=appointment.confirmed_date,
            confirmed_start_time=appointment.confirmed_start_time,
            confirmed_end_time=appointment.confirmed_end_time,
            confirmed_at=appointment.confirmed_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"약속 확정 실패: {str(e)}")
