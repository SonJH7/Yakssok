from datetime import date, datetime, time, timedelta
from typing import List, Dict, Set, Optional, Any
from collections import defaultdict

from app.models.user_model import User
from app.services.google_calendar_service import GoogleCalendarService


class ScheduleAnalyzer:
    DEFAULT_WORK_START = "00:00"
    DEFAULT_WORK_END = "23:59"
    MIN_SLOT_DURATION_MINUTES = 30
    GRID_INTERVAL_MINUTES = 15

    @staticmethod
    async def calculate_available_slots(
        user: User,
        candidate_dates: List[date],
        work_hours_start: str = DEFAULT_WORK_START,
        work_hours_end: str = DEFAULT_WORK_END,
        timezone: str = "Asia/Seoul",
    ) -> Optional[dict]:
        if not candidate_dates:
            return None

        try:
            # Access token 갱신
            access_token = await GoogleCalendarService.refresh_access_token(
                user.google_refresh_token
            )

            # 시간 범위 설정
            time_min = (
                datetime.combine(min(candidate_dates), time.min).isoformat() + "Z"
            )
            time_max = (
                datetime.combine(max(candidate_dates), time.max).isoformat() + "Z"
            )

            # Google Calendar 이벤트 조회
            calendar_response = await GoogleCalendarService.list_primary_events(
                access_token=access_token,
                time_min=time_min,
                time_max=time_max,
                max_results=250,
                time_zone=timezone,
            )

            events = calendar_response.get("events", [])

            # 날짜별 이벤트 그룹화
            events_by_date = ScheduleAnalyzer._group_events_by_date(
                events, candidate_dates, timezone
            )

            # 각 날짜별 가용 시간 계산
            work_start = ScheduleAnalyzer._parse_time(work_hours_start)
            work_end = ScheduleAnalyzer._parse_time(work_hours_end)

            slots = []
            for candidate_date in sorted(candidate_dates):
                available_times = ScheduleAnalyzer._calculate_available_times_for_date(
                    candidate_date,
                    events_by_date.get(candidate_date, []),
                    work_start,
                    work_end,
                )

                if available_times:
                    slots.append(
                        {
                            "date": candidate_date.isoformat(),
                            "available_times": available_times,
                        }
                    )

            return {
                "timezone": timezone,
                "slots": slots,
                "calculated_at": datetime.now().isoformat(),
            }

        except Exception:
            return None

    @staticmethod
    def _group_events_by_date(
        events: List[Dict[str, Any]], candidate_dates: List[date], timezone: str
    ) -> Dict[date, List[Dict[str, Any]]]:
        events_by_date = defaultdict(list)

        for event in events:
            # All-day 이벤트 처리
            if "date" in event.get("start", {}):
                start_date_str = event["start"]["date"]
                end_date_str = event["end"]["date"]
                start_date = datetime.fromisoformat(start_date_str).date()
                end_date = datetime.fromisoformat(end_date_str).date()

                current = start_date
                while current < end_date:
                    if current in candidate_dates:
                        events_by_date[current].append(
                            {"start": "00:00", "end": "23:59", "all_day": True}
                        )
                    current += timedelta(days=1)

            # 시간 기반 이벤트 처리
            elif "dateTime" in event.get("start", {}):
                start_dt = datetime.fromisoformat(
                    event["start"]["dateTime"].replace("Z", "+00:00")
                )
                end_dt = datetime.fromisoformat(
                    event["end"]["dateTime"].replace("Z", "+00:00")
                )

                event_date = start_dt.date()
                if event_date in candidate_dates:
                    events_by_date[event_date].append(
                        {
                            "start": start_dt.strftime("%H:%M"),
                            "end": end_dt.strftime("%H:%M"),
                            "all_day": False,
                        }
                    )

        return events_by_date

    @staticmethod
    def _calculate_available_times_for_date(
        target_date: date,
        events: List[Dict[str, Any]],
        work_start: time,
        work_end: time,
    ) -> List[Dict[str, str]]:
        # All-day 이벤트가 있으면 해당 날짜 전체 불가
        if any(event.get("all_day") for event in events):
            return []

        # 기본 가용 시간: work_start부터 work_end까지
        busy_periods = []
        for event in events:
            start = ScheduleAnalyzer._parse_time(event["start"])
            end = ScheduleAnalyzer._parse_time(event["end"])
            busy_periods.append((start, end))

        busy_periods = ScheduleAnalyzer._merge_time_periods(busy_periods)

        # 가용 시간 계산
        available_periods = []
        current_time = work_start

        for busy_start, busy_end in sorted(busy_periods):
            # 현재 시간과 바쁜 시간 시작 사이가 가용 시간
            if current_time < busy_start:
                available_periods.append((current_time, busy_start))
            current_time = max(current_time, busy_end)

        # 마지막 바쁜 시간 이후부터 work_end까지
        if current_time < work_end:
            available_periods.append((current_time, work_end))

        # 30분 미만 슬롯 필터링 및 포맷 변환
        result = []
        for start, end in available_periods:
            duration = ScheduleAnalyzer._time_diff_minutes(start, end)
            if duration >= ScheduleAnalyzer.MIN_SLOT_DURATION_MINUTES:
                result.append(
                    {"start": start.strftime("%H:%M"), "end": end.strftime("%H:%M")}
                )

        return result

    @staticmethod
    def find_common_slots(
        user_slots: List[dict], min_duration_minutes: int
    ) -> List[Dict[str, Any]]:
        """
        여러 사용자의 가용시간 교집합 계산

        1. 15분 단위 그리드로 변환
        2. 각 시간대별 참여 가능 인원 카운트
        3. 연속된 블록 병합
        4. 정렬: 참여 인원 DESC, 시간 길이 DESC
        """
        if not user_slots:
            return []

        total_participants = len(user_slots)

        time_grid: Dict[str, Dict[str, Set[int]]] = defaultdict(
            lambda: defaultdict(set)
        )

        for user_data in user_slots:
            user_id = user_data["user_id"]
            slots = user_data["slots"]

            for slot in slots:
                date_str = slot["date"]
                available_times = slot["available_times"]

                for time_range in available_times:
                    start = ScheduleAnalyzer._parse_time(time_range["start"])
                    end = ScheduleAnalyzer._parse_time(time_range["end"])

                    # 15분 단위로 그리드 채우기
                    current = start
                    while current < end:
                        time_str = current.strftime("%H:%M")
                        time_grid[date_str][time_str].add(user_id)
                        current = ScheduleAnalyzer._add_minutes(
                            current, ScheduleAnalyzer.GRID_INTERVAL_MINUTES
                        )

        # 연속된 블록 찾기 및 병합
        optimal_slots = []
        for date_str, time_slots in time_grid.items():
            merged_blocks = ScheduleAnalyzer._merge_consecutive_time_blocks(
                date_str, time_slots, min_duration_minutes, total_participants
            )
            optimal_slots.extend(merged_blocks)

        # 정렬: 참여 인원 DESC, 시간 길이 DESC
        optimal_slots.sort(
            key=lambda x: (-x["participant_count"], -x["duration_minutes"])
        )

        return optimal_slots

    @staticmethod
    def _merge_consecutive_time_blocks(
        date_str: str,
        time_slots: Dict[str, Set[int]],
        min_duration_minutes: int,
        total_participants: int,
    ) -> List[Dict[str, Any]]:
        if not time_slots:
            return []

        # 시간순 정렬
        sorted_times = sorted(time_slots.keys())

        results: List[Dict[str, Any]] = []
        current_start: Optional[str] = None
        current_participants: Optional[Set[int]] = None
        prev_time: Optional[time] = None

        for time_str in sorted_times:
            participants = time_slots[time_str]
            current_time = ScheduleAnalyzer._parse_time(time_str)

            # 새로운 블록 시작
            if current_start is None:
                current_start = time_str
                current_participants = participants
                prev_time = current_time
                continue

            assert prev_time is not None
            assert current_participants is not None

            time_diff = ScheduleAnalyzer._time_diff_minutes(prev_time, current_time)
            if (
                time_diff == ScheduleAnalyzer.GRID_INTERVAL_MINUTES
                and participants == current_participants
            ):
                prev_time = current_time
            else:
                end_time = ScheduleAnalyzer._add_minutes(
                    prev_time, ScheduleAnalyzer.GRID_INTERVAL_MINUTES
                )
                ScheduleAnalyzer._add_block_if_valid(
                    results,
                    date_str,
                    current_start,
                    end_time.strftime("%H:%M"),
                    current_participants,
                    total_participants,
                    min_duration_minutes,
                )

                current_start = time_str
                current_participants = participants
                prev_time = current_time

        # 마지막 블록 처리
        if current_start is not None and prev_time is not None:
            assert current_participants is not None
            end_time = ScheduleAnalyzer._add_minutes(
                prev_time, ScheduleAnalyzer.GRID_INTERVAL_MINUTES
            )
            ScheduleAnalyzer._add_block_if_valid(
                results,
                date_str,
                current_start,
                end_time.strftime("%H:%M"),
                current_participants,
                total_participants,
                min_duration_minutes,
            )

        return results

    @staticmethod
    def _add_block_if_valid(
        results: List[Dict[str, Any]],
        date_str: str,
        start_str: str,
        end_str: str,
        participants: Set[int],
        total_participants: int,
        min_duration_minutes: int,
    ):
        start = ScheduleAnalyzer._parse_time(start_str)
        end = ScheduleAnalyzer._parse_time(end_str)
        duration = ScheduleAnalyzer._time_diff_minutes(start, end)

        if duration >= min_duration_minutes:
            participant_count = len(participants)
            results.append(
                {
                    "date": date_str,
                    "start_time": start_str,
                    "end_time": end_str,
                    "duration_minutes": duration,
                    "participant_count": participant_count,
                    "total_participants": total_participants,
                    "participant_ids": sorted(list(participants)),
                    "availability_percentage": round(
                        (participant_count / total_participants) * 100, 2
                    ),
                }
            )

    @staticmethod
    def _parse_time(time_str: str) -> time:
        # 시간 문자열을 time 객체로 파싱
        try:
            return datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            return time(0, 0)

    @staticmethod
    def _time_diff_minutes(start: time, end: time) -> int:
        # 두 시간의 차이를 분 단위로 계산
        start_minutes = start.hour * 60 + start.minute
        end_minutes = end.hour * 60 + end.minute
        return end_minutes - start_minutes

    @staticmethod
    def _add_minutes(t: time, minutes: int) -> time:
        dt = datetime.combine(date.today(), t)
        dt += timedelta(minutes=minutes)
        result = dt.time()

        # 자정을 넘어가면 23:59로 제한
        if dt.date() > date.today():
            return time(23, 59)

        return result

    @staticmethod
    def _merge_time_periods(periods: List[tuple]) -> List[tuple]:
        # 겹치는 시간 구간들을 병합
        if not periods:
            return []

        sorted_periods = sorted(periods)
        merged = [sorted_periods[0]]

        for current_start, current_end in sorted_periods[1:]:
            last_start, last_end = merged[-1]

            if current_start <= last_end:
                merged[-1] = (last_start, max(last_end, current_end))
            else:
                merged.append((current_start, current_end))

        return merged
