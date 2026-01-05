import secrets
import string
import json
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.appointment_model import Appointments, AppointmentDates, Participations
from app.schema.appointment_schema import AppointmentCreateRequest
from app.services.schedule_analyzer import ScheduleAnalyzer
from app.services.user_service import UserService


class AppointmentService:
    @staticmethod
    def generate_invite_code(length: int = 8) -> str:
        # 랜덤 초대 코드 생성
        characters = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(characters) for _ in range(length))

    @staticmethod
    async def create_appointment(
        request: AppointmentCreateRequest, creator_id: str, db: AsyncSession
    ) -> Appointments:
        # 약속 생성 및 후보 날짜 등록

        # 후보 날짜 검증
        if not request.candidate_dates:
            raise ValueError("최소 1개 이상의 후보 날짜가 필요합니다")

        # 고유한 초대 코드 생성
        invite_code = AppointmentService.generate_invite_code()

        # 초대 코드 중복 체크
        while await AppointmentService._is_invite_code_exists(invite_code, db):
            invite_code = AppointmentService.generate_invite_code()

        # 약속 생성
        appointment = Appointments(
            name=request.name,
            creator_id=creator_id,
            max_participants=request.max_participants,
            status="VOTING",
            invite_link=invite_code,
        )

        db.add(appointment)
        await db.flush()

        # 요청받은 날짜들을 후보 날짜로 등록
        candidate_dates = []
        for candidate_date in request.candidate_dates:
            appointment_date = AppointmentDates(
                appointment_id=appointment.id, candidate_date=candidate_date
            )
            db.add(appointment_date)
            candidate_dates.append(candidate_date)

        # 생성자 참여자목록에 반영
        creator_participation = Participations(
            user_id=creator_id, appointment_id=appointment.id, status="ATTENDING"
        )
        db.add(creator_participation)

        # 생성자의 가용 시간 계산
        try:
            user = await UserService.get_user_by_google_id(str(creator_id), db)
            if user and user.google_refresh_token:
                available_slots = await ScheduleAnalyzer.calculate_available_slots(
                    user=user, candidate_dates=candidate_dates
                )

                if available_slots:
                    creator_participation.available_slots = json.dumps(
                        available_slots, ensure_ascii=False
                    )
        except Exception:
            pass

        await db.commit()
        await db.refresh(appointment)

        return appointment

    @staticmethod
    async def _is_invite_code_exists(invite_code: str, db: AsyncSession) -> bool:
        # 초대 코드 중복 확인
        result = await db.execute(
            select(Appointments).where(Appointments.invite_link == invite_code)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_appointment_by_invite_code(
        invite_code: str, db: AsyncSession
    ) -> Appointments:
        # 초대 코드로 약속 조회
        result = await db.execute(
            select(Appointments).where(Appointments.invite_link == invite_code)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_appointment_dates(
        appointment_id: int, db: AsyncSession
    ) -> List[AppointmentDates]:
        # 약속의 모든 후보 날짜 조회
        result = await db.execute(
            select(AppointmentDates).where(
                AppointmentDates.appointment_id == appointment_id
            )
        )
        return result.scalars().all()

    @staticmethod
    async def join_appointment(
        invite_code: str, user_id: str, db: AsyncSession
    ) -> Participations:
        # 초대 코드로 약속 참여

        # 약속 조회
        appointment = await AppointmentService.get_appointment_by_invite_code(
            invite_code, db
        )
        if not appointment:
            raise ValueError("존재하지 않는 약속입니다")

        # 약속 상태 확인
        if appointment.status != "VOTING":
            raise ValueError("참여할 수 없는 약속입니다")

        # 이미 참여했는지 확인
        existing = await AppointmentService._get_participation(
            user_id, appointment.id, db
        )
        if existing:
            raise ValueError("이미 참여한 약속입니다")

        # 최대 참여자 수 확인
        if appointment.max_participants:
            current_count = await AppointmentService._get_participation_count(
                appointment.id, db
            )
            if current_count >= appointment.max_participants:
                raise ValueError("참여 인원이 가득 찼습니다")

        # 참여자 추가
        participation = Participations(
            user_id=user_id, appointment_id=appointment.id, status="ATTENDING"
        )
        db.add(participation)

        # 가용 시간 계산
        try:
            user = await UserService.get_user_by_google_id(str(user_id), db)
            if user and user.google_refresh_token:
                candidate_dates = await AppointmentService.get_appointment_dates(
                    appointment.id, db
                )

                available_slots = await ScheduleAnalyzer.calculate_available_slots(
                    user=user,
                    candidate_dates=[ad.candidate_date for ad in candidate_dates],
                )

                if available_slots:
                    participation.available_slots = json.dumps(
                        available_slots, ensure_ascii=False
                    )
        except Exception:
            pass

        await db.commit()
        await db.refresh(participation)

        return participation

    @staticmethod
    async def _get_participation(
        user_id: str, appointment_id: int, db: AsyncSession
    ) -> Participations:
        # 특정 사용자의 참여 정보 조회
        result = await db.execute(
            select(Participations).where(
                Participations.user_id == user_id,
                Participations.appointment_id == appointment_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _get_participation_count(appointment_id: int, db: AsyncSession) -> int:
        # 약속의 참여자 수 조회
        from sqlalchemy import func

        result = await db.execute(
            select(func.count(Participations.id)).where(
                Participations.appointment_id == appointment_id
            )
        )
        return result.scalar()

    @staticmethod
    async def delete_appointment(
        invite_code: str, user_id: str, db: AsyncSession
    ) -> bool:
        # 약속 삭제
        appointment = await AppointmentService.get_appointment_by_invite_code(
            invite_code, db
        )
        if not appointment:
            raise ValueError("존재하지 않는 약속입니다")

        # 생성자 확인
        if appointment.creator_id != user_id:
            raise ValueError("약속 생성자만 삭제할 수 있습니다")

        # 약속 삭제
        await db.delete(appointment)
        await db.commit()

        return True

    @staticmethod
    async def get_appointment_detail_with_availability(
        invite_code: str, db: AsyncSession
    ) -> dict:
        # 약속 조회
        appointment = await AppointmentService.get_appointment_by_invite_code(
            invite_code, db
        )
        if not appointment:
            raise ValueError("존재하지 않는 약속입니다")

        # 후보 날짜 조회
        candidate_dates = await AppointmentService.get_appointment_dates(
            appointment.id, db
        )
        candidate_dates_list = sorted([ad.candidate_date for ad in candidate_dates])

        # 모든 참여자 조회
        result = await db.execute(
            select(Participations).where(
                Participations.appointment_id == appointment.id
            )
        )
        all_participations = result.scalars().all()
        total_participants = len(all_participations)

        # 가용시간 데이터가 있는 참여자 수
        participants_with_data = sum(1 for p in all_participations if p.available_slots)

        # 각 날짜별 가용성 계산
        date_availabilities = []
        for candidate_date in candidate_dates_list:
            available_count = 0

            # 각 참여자의 available_slots를 확인
            for participation in all_participations:
                if not participation.available_slots:
                    continue

                try:
                    slots_data = json.loads(participation.available_slots)
                    slots = slots_data.get("slots", [])

                    # 해당 날짜에 가용 시간이 있는지 확인
                    for slot in slots:
                        if slot["date"] == candidate_date.isoformat():
                            # available_times가 비어있지 않으면 가용
                            if slot.get("available_times"):
                                available_count += 1
                            break
                except Exception:
                    pass

            # availability 상태 결정
            if available_count == 0:
                availability = "none"
            elif available_count == total_participants:
                availability = "all"
            else:
                availability = "partial"

            date_availabilities.append(
                {
                    "date": candidate_date,
                    "availability": availability,
                    "available_count": available_count,
                    "total_count": total_participants,
                }
            )

        return {
            "id": appointment.id,
            "name": appointment.name,
            "creator_id": appointment.creator_id,
            "max_participants": appointment.max_participants,
            "status": appointment.status,
            "invite_link": appointment.invite_link,
            "total_participants": total_participants,
            "participants_with_data": participants_with_data,
            "dates": date_availabilities,
        }

    @staticmethod
    async def calculate_optimal_times(
        appointment_id: int,
        min_duration_minutes: int,
        db: AsyncSession,
        time_range_start: str = None,
        time_range_end: str = None,
    ) -> List[dict]:
        result = await db.execute(
            select(Participations)
            .where(Participations.appointment_id == appointment_id)
            .where(Participations.available_slots.isnot(None))
        )
        participations = result.scalars().all()

        if not participations:
            return []

        # JSON 파싱
        all_slots = []
        for p in participations:
            try:
                slots_data = json.loads(p.available_slots)
                filtered_slots = AppointmentService._filter_slots_by_time_range(
                    slots_data["slots"], time_range_start, time_range_end
                )
                all_slots.append({"user_id": p.user_id, "slots": filtered_slots})
            except Exception:
                pass

        # 교집합 계산
        optimal_times = ScheduleAnalyzer.find_common_slots(
            all_slots, min_duration_minutes
        )

        return optimal_times

    @staticmethod
    def _filter_slots_by_time_range(
        slots: List[dict], time_range_start: str = None, time_range_end: str = None
    ) -> List[dict]:
        # 저장된 가용 시간 슬롯을 시간대 필터로 제한
        if not time_range_start and not time_range_end:
            return slots

        from datetime import datetime

        filter_start = (
            datetime.strptime(time_range_start, "%H:%M").time()
            if time_range_start
            else datetime.strptime("00:00", "%H:%M").time()
        )
        filter_end = (
            datetime.strptime(time_range_end, "%H:%M").time()
            if time_range_end
            else datetime.strptime("23:59", "%H:%M").time()
        )

        filtered_slots = []
        for slot in slots:
            date_str = slot["date"]
            filtered_times = []

            for time_range in slot.get("available_times", []):
                start_time = datetime.strptime(time_range["start"], "%H:%M").time()
                end_time = datetime.strptime(time_range["end"], "%H:%M").time()

                # 필터 범위와 겹치는 부분만 추출
                new_start = max(start_time, filter_start)
                new_end = min(end_time, filter_end)

                # 유효한 범위가 있으면 추가
                if new_start < new_end:
                    filtered_times.append(
                        {
                            "start": new_start.strftime("%H:%M"),
                            "end": new_end.strftime("%H:%M"),
                        }
                    )

            if filtered_times:
                filtered_slots.append(
                    {"date": date_str, "available_times": filtered_times}
                )

        return filtered_slots

    @staticmethod
    async def confirm_appointment(
        invite_code: str,
        confirmed_date: str,
        confirmed_start_time: str,
        confirmed_end_time: str,
        user_id: str,
        db: AsyncSession,
    ) -> Appointments:
        from datetime import datetime

        # 약속 조회
        appointment = await AppointmentService.get_appointment_by_invite_code(
            invite_code, db
        )
        if not appointment:
            raise ValueError("존재하지 않는 약속입니다")

        # 생성자 확인
        if appointment.creator_id != user_id:
            raise ValueError("약속 생성자만 확정할 수 있습니다")

        # 이미 확정된 약속인지 확인
        if appointment.status == "CONFIRMED":
            raise ValueError("이미 확정된 약속입니다")
        
        
        # 약속 확정
        appointment.status = "CONFIRMED"
        appointment.confirmed_date = confirmed_date
        appointment.confirmed_start_time = confirmed_start_time
        appointment.confirmed_end_time = confirmed_end_time
        appointment.confirmed_at = datetime.now()

        await db.commit()
        await db.refresh(appointment)

        return appointment

    @staticmethod
    async def get_my_appointments(user_id: str, db: AsyncSession) -> List[Appointments]:
        # 내가 참여한 약속 목록 조회
        result = await db.execute(
            select(Appointments)
            .join(Participations, Appointments.id == Participations.appointment_id)
            .where(Participations.user_id == user_id)
            .order_by(Appointments.created_at.desc())
        )
        appointments = result.scalars().all()

        return appointments

    @staticmethod
    async def sync_my_schedules(user_id: str, db: AsyncSession) -> dict:
        # 내가 참여한 모든 약속의 일정 동기화

        user = await UserService.get_user_by_google_id(str(user_id), db)
        if not user or not user.google_refresh_token:
            raise ValueError("구글 캘린더 연동이 필요합니다")

        # 참여 중인 약속 조회
        result = await db.execute(
            select(Appointments)
            .join(Participations, Appointments.id == Participations.appointment_id)
            .where(Participations.user_id == user_id)
            .where(Appointments.status == "VOTING")
        )
        appointments = result.scalars().all()

        updated_count = 0
        failed_count = 0

        # 각 약속에 대해 일정 재계산
        for appointment in appointments:
            try:
                participation = await AppointmentService._get_participation(
                    user_id, appointment.id, db
                )

                if not participation:
                    failed_count += 1
                    continue

                candidate_dates_obj = await AppointmentService.get_appointment_dates(
                    appointment.id, db
                )
                candidate_dates = [ad.candidate_date for ad in candidate_dates_obj]

                available_slots = await ScheduleAnalyzer.calculate_available_slots(
                    user=user, candidate_dates=candidate_dates
                )

                if available_slots:
                    participation.available_slots = json.dumps(
                        available_slots, ensure_ascii=False
                    )
                    updated_count += 1
                else:
                    failed_count += 1

            except Exception:
                failed_count += 1

        await db.commit()

        return {
            "total_appointments": len(appointments),
            "updated_count": updated_count,
            "failed_count": failed_count,
        }
