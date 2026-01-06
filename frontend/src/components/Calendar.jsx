
import React, { useCallback, useEffect, useRef, useState } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { API_BASE_URL } from '../config/api';
import './Calendar.css';

const Calendar = ({ events: initialEvents = [] , onEventSelect }) => {
  const calendarRef = useRef(null);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [activeView, setActiveView] = useState('dayGridMonth');
  const [dateRange, setDateRange] = useState(null);
  const [events, setEvents] = useState(initialEvents);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [reauthUrl, setReauthUrl] = useState(null);
  const [headerTransitionClass, setHeaderTransitionClass] = useState('');
  const [bodyTransitionClass, setBodyTransitionClass] = useState('');

  const normalizeEvents = useCallback(
    (items = []) =>
      items
        .map((item) => {
          const isAllDay = Boolean(item?.start?.date);
          let start = item?.start?.dateTime || item?.start?.date;
          let end = item?.end?.dateTime || item?.end?.date;

          if (!start) return null;

          if (isAllDay) {
            const startDateStr = item.start.date;
            const endDateStr =
              item.end?.date ||
              new Date(new Date(startDateStr).getTime() + 24 * 60 * 60 * 1000)
                .toISOString()
                .slice(0, 10);

            start = `${startDateStr}T00:00:00`;
            end = `${endDateStr}T00:00:00`;
          }

          return {
            id: item.id || `${start}-${item.summary}`,
            title: item.summary || '제목 없음',
            start,
            end,
            allDay: false,
            extendedProps: {
              isAllDay,
            },
          };
        })
        .filter(Boolean),
    []
  );

  // JWT 사용하여 구글 캘린더 API 호출
  const fetchCalendarEvents = useCallback(
    async ({ start, end }) => {
      const token = localStorage.getItem('access_token');

      if (!token) {
        setError('로그인이 필요해요.');
        return;
      }

      if (!start || !end) {
        return;
      }

      setIsLoading(true);
      setError(null);
      setReauthUrl(null);

      try {
        const aggregateEvents = [];
        let pageToken = null;

        // 페이징 처리하며 여러 번 API 호출
        do {
          const params = new URLSearchParams({
            time_min: start.toISOString(),
            time_max: end.toISOString(),
            max_results: '50',
          });

          if (pageToken) {
            params.set('page_token', pageToken);
          }

          // 실제 API 호출, JWT 인증 요청
          const response = await fetch(
            `${API_BASE_URL}/calendar/events?${params.toString()}`,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          );

          const data = await response.json();

          if (!response.ok) {
            const message = data?.detail || '캘린더를 불러오지 못했어요.';
            setError(message);
            if (data?.reauthUrl) {
              setReauthUrl(data.reauthUrl);
            }
            return;
          }

          if (Array.isArray(data?.events)) {
            aggregateEvents.push(...data.events);
          }
          pageToken = data?.nextPageToken || null;
        } while (pageToken);

        // JWT 인증 성공 시 받은 데이터 화면에 반영
        setEvents(normalizeEvents(aggregateEvents));
        setReauthUrl(null);
      } catch {
        setError('캘린더를 불러오는 중 오류가 발생했어요.');
      } finally {
        setIsLoading(false);
      }
    },
    [normalizeEvents]
  );

  // 초기화: 오늘 날짜로 이동
  useEffect(() => {
    if (calendarRef.current) {
      const calendarApi = calendarRef.current.getApi();
      calendarApi.today();
      setCurrentDate(calendarApi.getDate());
    }
  }, []);

  useEffect(() => {
    if (dateRange) {
      fetchCalendarEvents(dateRange);
    }
  }, [dateRange, fetchCalendarEvents]);

  // 월/년도 표시 포맷팅
  const formatMonthAndYear = (date) => {
    const month = date.toLocaleString('ko-KR', { month: 'long' });
    const year = date.getFullYear();
    return { month, year };
  };
  const { month, year } = formatMonthAndYear(currentDate);

  const triggerSectionTransitions = useCallback(() => {
    setHeaderTransitionClass('');
    setBodyTransitionClass('');

    requestAnimationFrame(() => {
      setHeaderTransitionClass('fade-swap');
      setBodyTransitionClass('fade-swap');
    });
  }, []);

  useEffect(() => {
    triggerSectionTransitions();
  }, [currentDate, activeView, triggerSectionTransitions]);

  const handleViewChange = (view) => {
    if (calendarRef.current) {
      const api = calendarRef.current.getApi();
      api.changeView(view);
      setActiveView(view);
    }
  };

  const handleTodayClick = () => {
    const api = calendarRef.current?.getApi();
    api?.today();
    if (api) setCurrentDate(api.getDate());
  };

  const handlePrevClick = () => {
    const api = calendarRef.current?.getApi();
    api?.prev();
    if (api) setCurrentDate(api.getDate());
  };

  const handleNextClick = () => {
    const api = calendarRef.current?.getApi();
    api?.next();
    if (api) setCurrentDate(api.getDate());
  };

  const scrollToEarliestWeeklyEvent = useCallback(() => {
    if (activeView !== 'timeGridWeek' || !calendarRef.current || !events.length) return;

    const api = calendarRef.current.getApi();

    const weeklyEvents = events
      .map((e) => e.start && new Date(e.start))
      .filter(Boolean);

    if (weeklyEvents.length === 0) return;

    const earliest = weeklyEvents.reduce((min, d) => {
      const mins = d.getHours() * 60 + d.getMinutes();
      return Math.min(min, mins);
    }, Infinity);

    if (!Number.isFinite(earliest)) return;

    const hour = Math.floor(earliest / 60);
    const minute = earliest % 60;

    api.scrollToTime({ hours: hour, minutes: minute });
  }, [activeView, events]);


  // 주간 뷰 이동 시 가장 이른 일정 시간으로 자동 스크롤
  useEffect(() => {
    scrollToEarliestWeeklyEvent();
  }, [scrollToEarliestWeeklyEvent]);

  // 요일 헤더 커스텀
  const getDayHeaderContent = (info) => {
    const days = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일'];
    const dayName = days[info.date.getDay()];
    const dayNumber = info.date.getDate();

    if (info.view.type === 'dayGridMonth') {
      return <span className="monthly-header-dayname">{dayName}</span>;
    } else if (info.view.type === 'timeGridWeek') {
      return (
        <div className="weekly-header-content">
          <p className="weekly-header-dayname">{dayName}</p>
          <p className="weekly-header-daynumber">{dayNumber}일</p>
        </div>
      );
    }
    return null;
  };

  // 주간 캘린더 이벤트 렌더링 (색상 조건 추가)
  const renderEventContent = (arg) => {
    const { event, timeText, view } = arg;

    if (view.type === 'timeGridWeek') {
      const eventDate = new Date(event.start);
      eventDate.setHours(0, 0, 0, 0);

      const today = new Date();
      today.setHours(0, 0, 0, 0);

      let statusClass = "future-event";
      if (eventDate.getTime() === today.getTime()) {
        statusClass = "today-event";
      } else if (eventDate.getTime() < today.getTime()) {
        statusClass = "past-event";
      }

      const isAllDay = event.extendedProps?.isAllDay;
      const displayTimeText = isAllDay ? '00:00 - 24:00' : timeText;

      return (
        <div className={`custom-event-content ${statusClass}`}>
          <div className="event-title">{event.title}</div>
          {displayTimeText && (
            <div className="event-time-container">
              <span className="event-time-start">{displayTimeText}</span>
            </div>
          )}
        </div>
      );
    }

    return null;
  };

  //우측 사이드바 관련 클릭 처리 (월간)
  const openSidebarWithEventsOfDay = useCallback(
    (cellDate) => {
      const clicked = new Date(cellDate);
      clicked.setHours(0, 0, 0, 0);

      const dayEvents = (events || []).filter((e) => {
        if (!e?.start) return false;

        const eventStart = new Date(e.start);
        eventStart.setHours(0, 0, 0, 0);

        const hasEnd = Boolean(e.end);
        const eventEnd = hasEnd ? new Date(e.end) : new Date(e.start);
        eventEnd.setHours(0, 0, 0, 0);

        if (e.extendedProps?.isAllDay && hasEnd) {
          eventEnd.setDate(eventEnd.getDate() - 1);
        }

        return clicked.getTime() >= eventStart.getTime() &&
               clicked.getTime() <= eventEnd.getTime();
      })
      .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());

      if (dayEvents.length === 0) return;

      onEventSelect?.({
      type: "events",
      date: clicked,
      events: dayEvents.map((ev) => ({
        id: ev.id,
        title: ev.title,
        start: ev.start,
        end: ev.end,
        allDay: ev.allDay,
        extendedProps: ev.extendedProps,
      })),
    });
  },
  [events, onEventSelect]
  );

  return (
    <div className="w-full max-w-4xl p-6 bg-white rounded-lg shadow-xl">
      <div className="calendar-container">
        {/* 상단 커스텀 헤더 */}
        <div className={`custom-header ${headerTransitionClass}`}>
          <div className="custom-title-container">
            <span className="month">{month}</span>
            <span className="year">{year}</span>
          </div>

          <div className="view-toggle-buttons">
            <button
              onClick={() => handleViewChange('dayGridMonth')}
              className={activeView === 'dayGridMonth' ? 'active' : ''}
            >
              월간
            </button>
            <button
              onClick={() => handleViewChange('timeGridWeek')}
              className={activeView === 'timeGridWeek' ? 'active' : ''}
            >
              주간
            </button>
          </div>

          <div className="nav-buttons">
            <button onClick={handlePrevClick} className="nav-arrow">&lt;</button>
            <button onClick={handleTodayClick} className="today-button">오늘</button>
            <button onClick={handleNextClick} className="nav-arrow">&gt;</button>
          </div>
        </div>

        {error && (
          <div className="calendar-error">
            <span>{error}</span>
            {reauthUrl && (
              <button
                type="button"
                className="reauth-button"
                onClick={() => (window.location.href = reauthUrl)}
              >
                다시 인증하기
              </button>
            )}
          </div>
        )}

        {/* {isLoading && <div className="calendar-loading">구글 캘린더를 불러오는 중이예요...</div>} */}

        <div className={`calendar-surface ${bodyTransitionClass}`}>
          <FullCalendar
            ref={calendarRef}
            plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
            initialView="dayGridMonth"
            locale="ko"
            events={events}
            headerToolbar={false}
            datesSet={(info) => {
              setActiveView(info.view.type);
              setCurrentDate(info.view.currentStart);
              setDateRange({ start: info.view.currentStart, end: info.view.currentEnd });
            }}
            dayHeaderContent={getDayHeaderContent}
            eventContent={renderEventContent}
            eventDisplay="block"
            eventTimeFormat={{
              hour: '2-digit',
              minute: '2-digit',
              hour12: false,
            }}
            allDaySlot={false}
            slotLabelContent={(arg) => `${arg.date.getHours()}시`}
            slotMinTime="00:00:00"
            slotMaxTime="24:00:00"
            slotDuration="01:00:00"
            height={activeView === 'timeGridWeek' ? '800px' : 'auto'}
            handleWindowResize={true}

            //우측 사이드바 관련 클릭 처리 (주간)
            eventClick={(clickInfo) => {
              const ev = clickInfo.event;
              onEventSelect?.({
                type: "event",
                event: {
                  id: ev.id,
                  title: ev.title,
                  start: ev.start,
                  end: ev.end,
                  allDay: ev.allDay,
                  extendedProps: ev.extendedProps,
                },
              });
            }}

            // 월간 날짜 셀 커스텀
            dayCellContent={(arg) => {
              if (arg.view.type === 'dayGridMonth') {
                const cellDate = new Date(arg.date);
                cellDate.setHours(0, 0, 0, 0);

                const today = new Date();
                today.setHours(0, 0, 0, 0);

                if (!Array.isArray(events)) {
                  return arg.dayNumberText.replace("일", "");
                }

                const dayEvents = events.filter(e => {
                  if (!e.start) return false;
                  const eventStart = new Date(e.start);
                eventStart.setHours(0, 0, 0, 0);

                  const hasEnd = Boolean(e.end);
                  const eventEnd = hasEnd ? new Date(e.end) : new Date(e.start);
                  eventEnd.setHours(0, 0, 0, 0);

                  if (e.extendedProps?.isAllDay && hasEnd) {
                    eventEnd.setDate(eventEnd.getDate() - 1);
                  }

                  return (
                    cellDate.getTime() >= eventStart.getTime() &&
                    cellDate.getTime() <= eventEnd.getTime()
                  );
                });

                if (!dayEvents || dayEvents.length === 0) {
                  return <div className="date-number">{arg.dayNumberText.replace("일", "")}</div>;
                }

                const displayEvents = [...dayEvents]
                  .sort((a, b) => {
                    const aStart = a?.start ? new Date(a.start).getTime() : Number.POSITIVE_INFINITY;
                    const bStart = b?.start ? new Date(b.start).getTime() : Number.POSITIVE_INFINITY;

                    if (aStart !== bStart) return aStart - bStart;
                    return (a?.title || '').localeCompare(b?.title || '');
                  })
                  .slice(0, 2);

                let backgroundColor = "";
                let textColor = "#1F1F1F";

                if (cellDate.getTime() === today.getTime()) {
                  backgroundColor = "#F9CBAA";
                  textColor = "#FFFFFF";
                } else if (cellDate.getTime() < today.getTime()) {
                  backgroundColor = "#E9E9E3";
                  textColor = "#C4C5B7";
                } else {
                  backgroundColor = "#BBCEA0";
                  textColor = "#FFFFFF";
                }

              return (
                  <div
                    className="calendar-day-box"
                    style={{ backgroundColor, color: textColor }}
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      openSidebarWithEventsOfDay(arg.date);
                    }}
                  >
                    <div className="calendar-date-num" style={{ color: textColor }}>
                      {arg.dayNumberText.replace("일", "")}
                    </div>
                    <div className="calendar-event-list">
                      {displayEvents.map((ev, i) => (
                        <div
                          key={i}
                          className="calendar-event-title"
                          style={{ color: textColor }}
                        >
                          {ev.title}
                        </div>
                      ))}
                    </div>
                  </div>
                );
              }
              return arg.dayNumberText;
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default Calendar;