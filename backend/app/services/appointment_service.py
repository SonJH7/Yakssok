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
        appointment_id: int, min_duration_minutes: int, db: AsyncSession
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
                all_slots.append({"user_id": p.user_id, "slots": slots_data["slots"]})
            except Exception:
                pass

        # 교집합 계산
        optimal_times = ScheduleAnalyzer.find_common_slots(
            all_slots, min_duration_minutes
        )

        return optimal_times

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
