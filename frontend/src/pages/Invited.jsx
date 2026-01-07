import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import LogoIconWhite from "../assets/LogoIconWhite";
import EditIcon from "../assets/EditIcon";
import CreateEvent from '../components/CreateEvent';
import UpdateEvent from '../components/UpdateEvent';
import ExclamationIcon from '../assets/ExclamationIcon';
import CheckCircleIcon from '../assets/CheckCircleIcon';
import EmptyCircleIcon from '../assets/EmptyCircleIcon';
import QuestionIcon from '../assets/QuestionIcon';
import DateCheckIcon from '../assets/DateCheckIcon';
import { API_BASE_URL } from '../config/api';
import './Invited.css';

const CheckedBoxIcon = () => (
  <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
    <rect
      x="2"
      y="2"
      width="22"
      height="22"
      rx="2"
      stroke="#EEB1B1"
      strokeWidth="2.5"
    />

    <path
      d="M7 13.5L11 17.5L19 9.5"
      stroke="#EEB1B1"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const RadioCheckedIcon = () => (
  <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
    <rect
      x="2"
      y="2"
      width="22"
      height="22"
      rx="15"
      stroke="#EEB1B1"
      strokeWidth="2.5"
    />

    <path
      d="M7 13.5L11 17.5L19 9.5"
      stroke="#EEB1B1"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const EmptyBoxIcon = () => (
  <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
    <path
      d="M22.5652 24H3.43478C3.05425 24 2.68931 23.8488 2.42024 23.5798C2.15116 23.3107 2 22.9457 2 22.5652V3.43478C2 2.64087 2.64087 2 3.43478 2H22.5652C23.3572 2 24 2.64087 24 3.43478V22.5652C24 22.9457 23.8488 23.3107 23.5798 23.5798C23.3107 23.8488 22.9457 24 22.5652 24ZM4.86957 21.1304H21.1304V4.86957H4.86957V21.1304Z"
      fill="#E9E9E3"
    />
  </svg>
);

const RadioEmptyIcon = () => (
  <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
    <rect
      x="2"
      y="2"
      width="22"
      height="22"
      rx="15"
      stroke="#E9E9E3"
      strokeWidth="2.5"
    />
  </svg>
);

const Invited = () => {
  const { code } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const initialEvents = location.state ? location.state.events : [];
  const initialEventsWithId = initialEvents.map((event, index) => ({
    ...event,
    id: event.id || `generated-${index}-${Date.now()}`,
  }));

  // 초기 데이터 로드 (ID가 없으면 강제로 생성)
  const [allEvents, setAllEvents] = useState(initialEventsWithId);
  const [pendingAddEvents, setPendingAddEvents] = useState([]);
  const [pendingDeleteIds, setPendingDeleteIds] = useState([]);
  const [pendingUpdateEvents, setPendingUpdateEvents] = useState([]);

  const [partyName, setPartyName] = useState("");
  const [candidateDates, setCandidateDates] = useState([]);
 
  const [filteredEvents, setFilteredEvents] = useState([]); 
  
  const [activeMenuId, setActiveMenuId] = useState(null);

  const [popupPos, setPopupPos] = useState({ top: 0, left: 0 });
  const [menuTargetDate, setMenuTargetDate] = useState(null);

  const [viewMode, setViewMode] = useState('list');

  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [selectedDateEvents, setSelectedDateEvents] = useState([]);

  const [selectionContext, setSelectionContext] = useState(null);
  const [selectionValues, setSelectionValues] = useState([]);

  const [prevViewMode, setPrevViewMode] = useState(null);

  const isDeleteMode = selectionContext?.mode === 'delete';

  // 토큰 만료 여부 확인
  const isAccessTokenExpired = useCallback((token) => {
    if (!token) return true;

    const parts = token.split('.');
    if (parts.length < 2) return true;

    try {
      const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
      const exp = payload?.exp;

      if (!exp) return true;

      return Date.now() >= exp * 1000;
    } catch (error) {
      console.warn('토큰 만료 여부 확인 중 문제가 발생했습니다.', error);
      return true;
    }
  }, []);

  // 로그인 리다이렉트 처리
  const redirectToLogin = useCallback(() => {
    if (code) {
      sessionStorage.setItem('invite-code', code);
      sessionStorage.setItem('invite-redirect', `/invite/${code}`);
      navigate(`/login/${code}`, { replace: true });
    } else {
      sessionStorage.removeItem('invite-code');
      sessionStorage.setItem('invite-redirect', location.pathname + location.search);
      navigate('/login', { replace: true });
    }
  }, [code, navigate, location.pathname, location.search]);

  const ensureValidToken = useCallback(() => {
    const token = localStorage.getItem('access_token');

    if (!token || isAccessTokenExpired(token)) {
      localStorage.removeItem('access_token');
      redirectToLogin();
      return null;
    }

    return token;
  }, [isAccessTokenExpired, redirectToLogin]);

  useEffect(() => {
    const token = localStorage.getItem('access_token');

    if (!token || isAccessTokenExpired(token)) {
      localStorage.removeItem('access_token');
      redirectToLogin();
    }
  }, [code, navigate, redirectToLogin, isAccessTokenExpired]);

  // 초대 링크 기반 약속 정보 불러오기
  useEffect(() => {
    const token = localStorage.getItem('access_token');

    if (!code || !token) return;
    if (isAccessTokenExpired(token)) {
      localStorage.removeItem('access_token');
      redirectToLogin();
      return;
    }

    const fetchAppointment = async () => {
      if (!code) return;

      try {
        const res = await fetch(`${API_BASE_URL}/appointments/${code}/detail`);
        if (!res.ok) {
          console.error("약속 조회 실패", res.status);
          return;
        }

        const data = await res.json();
        setPartyName(data.name || "");

        if (data.dates && data.dates.length > 0) {
          const parsedDates = data.dates
            .map((item) => {
              const parsedDate = new Date(item.date);
              if (isNaN(parsedDate.getTime())) return null;

              return {
                date: parsedDate,
                availability: item.availability || "none",
                availableCount: item.available_count ?? 0,
                totalCount: item.total_count ?? 0,
              };
            })
            .filter(Boolean)
            .sort((a, b) => a.date.getTime() - b.date.getTime());

          if (parsedDates.length > 0) {
            setCandidateDates(parsedDates);
          }
        }
      } catch (error) {
        console.error("약속 정보를 불러오지 못했어요", error);
      }
    };

    fetchAppointment();
  }, [code]);

  const normalizeEvents = useCallback((items = []) =>
    items
      .map((item) => {
        const start = item?.start?.dateTime || item?.start?.date || item?.start;
        const end = item?.end?.dateTime || item?.end?.date || item?.end;

        if (!start) return null;

        return {
          id: item.id || `${start}-${item.summary || item.title}`,
          title: item.summary || item.title || '제목 없음',
          start,
          end,
          allDay: Boolean(item?.start?.date),
        };
      })
      .filter(Boolean),
  []);

  const fetchUserEvents = useCallback(async () => {
    if (candidateDates.length === 0) return;

    const token = localStorage.getItem('access_token');
    if (!token) {
      console.warn('access_token이 없어 캘린더를 불러올 수 없습니다.');
      return;
    }

    const sortedDates = [...candidateDates]
      .map((item) => new Date(item.date))
      .filter((d) => !isNaN(d.getTime()))
      .sort((a, b) => a.getTime() - b.getTime());

    if (sortedDates.length === 0) return;

    const rangeStart = new Date(sortedDates[0]);
    rangeStart.setHours(0, 0, 0, 0);
    const rangeEnd = new Date(sortedDates[sortedDates.length - 1]);
    rangeEnd.setHours(23, 59, 59, 999);

    try {
      const aggregated = [];
      let pageToken = null;

      do {
        const params = new URLSearchParams({
          time_min: rangeStart.toISOString(),
          time_max: rangeEnd.toISOString(),
          max_results: '50',
        });

        if (pageToken) {
          params.set('page_token', pageToken);
        }

        const response = await fetch(`${API_BASE_URL}/calendar/events?${params.toString()}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.status === 401) {
          localStorage.removeItem('access_token');
          redirectToLogin();
          return;
        }

        const data = await response.json();

        if (!response.ok) {
          const message = data?.detail || '캘린더를 불러오지 못했습니다.';
          console.error(message);
          return;
        }

        if (Array.isArray(data?.events)) {
          aggregated.push(...data.events);
        }

        pageToken = data?.nextPageToken || null;
      } while (pageToken);

      setAllEvents(normalizeEvents(aggregated));
    } catch (error) {
      console.error('캘린더 불러오기 중 오류가 발생했습니다.', error);
    }
  }, [candidateDates, normalizeEvents, redirectToLogin]);

  useEffect(() => {
    fetchUserEvents();
  }, [fetchUserEvents]);

  const isEventCoveringDate = (event, date) => {
    if (!event?.start) return false;

    const normalizeMidnight = (value) => {
      const normalized = new Date(value);
      normalized.setHours(0, 0, 0, 0);
      return normalized;
    };

    const targetDate = normalizeMidnight(date);
    const eventStart = normalizeMidnight(event.start);
    const eventEnd = event.end ? normalizeMidnight(event.end) : eventStart;

    if (event.allDay) {
      eventEnd.setDate(eventEnd.getDate() - 1);
    }

    const [startMs, endMs] = [eventStart.getTime(), eventEnd.getTime()];

    // 종료일이 시작일보다 앞선 경우에는 시작일만 비교
    if (endMs < startMs) {
      return targetDate.getTime() === startMs;
    }

    return targetDate.getTime() >= startMs && targetDate.getTime() <= endMs;
  };

  useEffect(() => {
    if (candidateDates.length === 0) {
      setFilteredEvents([]);
      return;
    }

    const candidateDateSet = new Set(
      candidateDates.map((item) => {
        const normalized = new Date(item.date);
        normalized.setHours(0, 0, 0, 0);
        return normalized.getTime();
      })
    );

    const filtered = allEvents.filter((event) =>
      candidateDates.some((candidate) => isEventCoveringDate(event, candidate.date))
    );
    setFilteredEvents(filtered); 
  }, [allEvents, candidateDates]); 

  const getEventsForDate = (date) => {
    return filteredEvents.filter((event) => isEventCoveringDate(event, date));
  };
  
  const getEventTitleForDate = (date) => {
    const dayEvents = getEventsForDate(date);
    return dayEvents.length > 0 
      ? dayEvents.map(e => e.title).join(", ") 
      : "약속 없음";
  };

  const formatEventTime = (event) => {
    if (!event?.start) return '';

    const startDate = new Date(event.start);
    const endDate = event.end ? new Date(event.end) : null;

    if (Number.isNaN(startDate.getTime())) return event.title;

    const startTime = startDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const endTime = endDate && !Number.isNaN(endDate.getTime())
      ? endDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : '';

    return endTime ? `${startTime} - ${endTime}` : startTime;
  };

  const getDateNumber = (date) => {
    if (!date) return '0';
    const d = new Date(date);
    return Number.isNaN(d.getTime()) ? '0' : d.getDate();
  };

  
  const isSelectedId = (id) => selectionValues.includes(id);

  const syncMySchedules = async () => {
    const token = ensureValidToken();
    if (!token) return null;

    const response = await fetch(`${API_BASE_URL}/appointments/sync-my-schedules`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json().catch(() => null);

    if (response.status === 401) {
      localStorage.removeItem('access_token');
      redirectToLogin();
      return null;
    }

    if (!response.ok) {
      const message = data?.detail || '약속 일정 동기화에 실패했습니다.';
      throw new Error(message);
    }

    return data;
  };

  const joinAppointment = async () => {
    const token = ensureValidToken();
    if (!token) return null;

    const response = await fetch(`${API_BASE_URL}/appointments/join`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ invite_code: code }),
    });

    const data = await response.json().catch(() => null);

    if (response.status === 401) {
      localStorage.removeItem('access_token');
      redirectToLogin();
      return null;
    }

    if (!response.ok) {
      const message = data?.detail || '약속 참여에 실패했습니다.';

      if (response.status === 400 && message.includes('이미 참여한 약속입니다')) {
        return null;
      }

      throw new Error(message);
    }

    return data;
  };

  const toggleMenu = (e, date) => {
    e.stopPropagation(); 

    if (isDeleteMode) return;

    const dateMs = date.getTime();

    if (activeMenuId === dateMs) {
      setActiveMenuId(null);
      return;
    }

    const eventBox = e.currentTarget.closest('.event-box');
    const rect = e.currentTarget.getBoundingClientRect();
    setPopupPos({
      top: rect.top -155, 
      left: rect.left + 50 
    });

    setMenuTargetDate(date);
    setActiveMenuId(dateMs);
  };

  const handleAddClick = (date) => {
    setSelectedDate(date);
    setViewMode('create'); 
    setActiveMenuId(null);
  };

  const handleEditClick = (date, eventTitleString) => {
    const dayEvents = getEventsForDate(date);

    if (dayEvents.length === 0) {
      alert("수정할 약속이 없어요.");
      return;
    }

    if (dayEvents.length === 1) {
      setSelectedEvent(dayEvents[0]);
      setSelectedDateEvents(dayEvents);
      setPrevViewMode('list');
      setViewMode('update');
      setActiveMenuId(null);
      return;
    }

    setSelectionContext({ mode: 'edit', date, events: dayEvents });
    setSelectionValues([dayEvents[0].id]);
    setViewMode('select-edit');
    setActiveMenuId(null);
  };

  const enterDeleteMode = (date) => {
    const dayEvents = getEventsForDate(date);
    if (dayEvents.length === 0) {
        alert("삭제할 약속이 없어요.");
        return;
    }

    setSelectionContext({ mode: 'delete', date, events: dayEvents });

    if (dayEvents.length === 1) {
      setSelectionValues([dayEvents[0].id]);
    } else {
      setSelectionValues([]);
    }

    setViewMode('select-edit');
  };

  const confirmDelete = (ids) => {
    if (!ids || ids.length === 0) {
      alert("선택된 일정이 없어요.");
      return;
    }

    const updatedPendingAdds = pendingAddEvents.filter(
      (event) => !ids.includes(event.id)
    );

    const newPendingDeleteIds = [
      ...pendingDeleteIds,
      ...ids.filter(
        (id) =>
          !pendingDeleteIds.includes(id) &&
          pendingAddEvents.every((event) => event.id !== id)
      ),
    ];

    const updatedEvents = allEvents.filter(
      (event) => !ids.includes(event.id)
    );

    setAllEvents(updatedEvents);
    setPendingAddEvents(updatedPendingAdds);
    setPendingDeleteIds(newPendingDeleteIds);
    setPendingUpdateEvents((prev) =>
      prev.filter((item) => !ids.includes(item.id))
    );
    setSelectionContext(null);
    setSelectionValues([]);
    setViewMode('list');

    setActiveMenuId(null);
    setMenuTargetDate(null);
  };

  const toggleSelectionValue = (id) => {
    if (!selectionContext) return;

    if (selectionContext.mode === 'edit') {
      setSelectionValues([id]);
      return;
    }

    setSelectionValues((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleSelectionConfirm = () => {
    if (!selectionContext) return;

    if (selectionContext.mode === 'edit') {
      const target = selectionContext.events.find((evt) => evt.id === selectionValues[0]);
      if (!target) {
        alert('수정할 일정을 선택해주세요.');
        return;
      }
      setSelectedEvent(target);
      setSelectedDateEvents(selectionContext.events);
      setPrevViewMode('select-edit');
      setViewMode('update');
    } else if (selectionContext.mode === 'delete') {
      if (selectionValues.length === 0) {
        return;
      }
      confirmDelete(selectionValues); 
      setSelectionContext(null);
      setSelectionValues([]);
      setViewMode('list');

      setActiveMenuId(null);
      setMenuTargetDate(null);
    }

  };

  const handleSelectionCancel = () => {
    setSelectionContext(null);
    setSelectionValues([]);
  };

  const saveNewEvent = (eventData) => {
    const newEvent = { ...eventData, id: `temp-${Date.now()}` };
    setAllEvents([...allEvents, newEvent]);
    setPendingAddEvents([...pendingAddEvents, newEvent]);
    setViewMode('list');
  };

  const updateEvent = (updatedEvent, updatePayload = {}) => {
    const isNewlyAdded = pendingAddEvents.some((event) => event.id === updatedEvent.id);

    if (isNewlyAdded) {
      setPendingAddEvents((prev) =>
        prev.map((event) => (event.id === updatedEvent.id ? updatedEvent : event))
      );
      setAllEvents((prev) =>
        prev.map((event) => (event.id === updatedEvent.id ? updatedEvent : event))
      );
      setViewMode('list');
      return;
    }

    setPendingUpdateEvents((prev) => {
      const remaining = prev.filter((item) => item.id !== updatedEvent.id);
      const hasPayload = updatePayload && Object.keys(updatePayload).length > 0;

      return hasPayload
        ? [...remaining, { id: updatedEvent.id, payload: updatePayload }]
        : remaining;
    });

    setAllEvents((prev) =>
      prev.map((event) => (event.id === updatedEvent.id ? updatedEvent : event))
    );
    setViewMode('list');
  };

  const syncWithGoogleCalendar = async () => {
    const token = ensureValidToken();
    if (!token) return;

    if (
      pendingAddEvents.length === 0 &&
      pendingDeleteIds.length === 0 &&
      pendingUpdateEvents.length === 0
    ) {
      alert('추가, 삭제하거나 수정한 일정은 없어요.');
      return;
    }

    try {
      for (const update of pendingUpdateEvents) {
        const res = await fetch(`${API_BASE_URL}/calendar/events/${update.id}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(update.payload),
        });

        if (res.status === 401) {
          localStorage.removeItem('access_token');
          redirectToLogin();
          return;
        }

        if (!res.ok) {
          const message = (await res.json())?.detail || '일정 수정에 실패했습니다.';
          throw new Error(message);
        }
      }

      for (const deleteId of pendingDeleteIds) {
        const res = await fetch(`${API_BASE_URL}/calendar/events/${deleteId}`, {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (res.status === 401) {
          localStorage.removeItem('access_token');
          redirectToLogin();
          return;
        }

        if (!res.ok) {
          const message = (await res.json())?.detail || '일정 삭제에 실패했습니다.';
          throw new Error(message);
        }
      }

      for (const event of pendingAddEvents) {
        const payload = {
          summary: event.title || event.summary || '제목 없음',
          description: event.description,
          start: {
            dateTime: new Date(event.start).toISOString(),
            timeZone: 'Asia/Seoul',
          },
          end: {
            dateTime: new Date(event.end || event.start).toISOString(),
            timeZone: 'Asia/Seoul',
          },
        };

        const res = await fetch(`${API_BASE_URL}/calendar/events`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(payload),
        });

        if (res.status === 401) {
          localStorage.removeItem('access_token');
          redirectToLogin();
          return;
        }

        if (!res.ok) {
          const message = (await res.json())?.detail || '일정 추가에 실패했습니다.';
          throw new Error(message);
        }
      }

      await fetchUserEvents();
      setPendingAddEvents([]);
      setPendingDeleteIds([]);
      setPendingUpdateEvents([]);
      alert('구글 캘린더와 동기화되었어요. 잠시만 기다려주세요.');
    } catch (error) {
      console.error(error);
      alert(error.message || '캘린더 동기화 중 문제가 발생했습니다.');
    }
  };

  const handleConfirm = async () => {
    try {
      const token = ensureValidToken();
      if (!token) return;
      await joinAppointment(); // 약속 참여 처리
      await syncWithGoogleCalendar(); // 구글 캘린더 반영
      const syncResult = await syncMySchedules(); // 내가 참여한 약속 일정 동기화

      if (syncResult) {
        alert(
          `총 ${syncResult.total_appointments}개의 약속 중 ${syncResult.updated_count}개를 동기화했어요.\n실패: ${syncResult.failed_count}개`
        );
      }

      navigate(`/result/${code}`);    // 결과 페이지로 이동
    } catch (e) {
      alert(e?.message || "처리 중 오류가 발생했습니다.");
    }
  };

  if (viewMode === 'create') {
    return (
      <div className="invite-view-wrapper">
        <div className="invite-view-panel">
          <div className="invite-content-shell invite-fade-soft" key="create">
            <CreateEvent
              date={selectedDate}
              onSave={saveNewEvent}
              onCancel={() => setViewMode('list')}
            />
          </div>
        </div>
      </div>
    );
  }

  if (viewMode === 'select-edit' && selectionContext) {
    const isMultiEdit =
      selectionContext.mode === 'edit' &&
      selectionContext.events.length > 1;
    const isDeleteSelection = selectionContext.mode === 'delete';
    const dateNum = getDateNumber(selectionContext.date);
    const selectedEditId = selectionContext.mode === 'edit' ? selectionValues[0] : null;
    const orderedSelectionEvents = selectedEditId
      ? [
          ...selectionContext.events.filter((evt) => evt.id === selectedEditId),
          ...selectionContext.events.filter((evt) => evt.id !== selectedEditId),
        ]
      : selectionContext.events;

    return (
      <div className="event-page-overlay">
        <div className="event-page-container">
          {/* 상단 질문 영역 */}
          <div className="create-header-wrapper">
            <div className="header-icon">
              {selectionContext.mode === 'delete' ? <ExclamationIcon /> : <QuestionIcon />}
            </div>
            <h2 className="header-title-text">
              {selectionContext.mode === 'delete'
                ? <>어떤 일정을<br />삭제하시겠어요?</>
                : <>어떤 일정을<br />수정하시겠어요?</>}
            </h2>
            <p className="header-sub-text">약속이 여러 개시네요</p>
          </div>

        {/* 날짜 카드 */}
          <div
            className="selected-date-box"
            style={{ backgroundColor: isMultiEdit || isDeleteSelection ? '#F9CBAA' : 'transparent' }}
          >
            <div className="selected-date-num" style={{ color: '#FFFFFF' }}>
              {dateNum}
            </div>
            <div className="date-check-icon"><DateCheckIcon /></div>
            <div className="selected-event-title-list" style={{ color: '#FFFFFF' }}>
              {orderedSelectionEvents.map((evt) => (
                <span
                  key={evt.id}
                  className="selected-event-title"
                >
                  {evt.title}
                </span>
              ))}
            </div>
          </div>

        {/* 일정 리스트 (radio 선택) */}
          <div className="selection-list">
            {selectionContext.events.map((evt) => (
              <div
                key={evt.id}
                className={`selection-item ${isSelectedId(evt.id) ? 'selected' : ''}`}
                onClick={() => {
                  if (selectionContext.mode === 'edit') {
                    setSelectionValues([evt.id]); // 라디오
                  } else {
                    setSelectionValues((prev) =>
                      prev.includes(evt.id)
                        ? prev.filter((id) => id !== evt.id)
                        : [...prev, evt.id]
                    ); // 체크박스
                  }
                }}
              >
                <div className="selection-info">
                  <span className="selection-title">{evt.title}</span>
                  <span className="selection-time">{formatEventTime(evt)}</span>
                </div>

                <div className="selection-check">
                  {selectionContext.mode === 'edit' ? (
                    isSelectedId(evt.id) ? <RadioCheckedIcon /> : <RadioEmptyIcon />
                  ) : (
                    isSelectedId(evt.id) ? <CheckedBoxIcon /> : <EmptyBoxIcon />
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* 하단 버튼 */}
          <div className="button-group">
            {selectionContext.mode === 'delete' ? (
              <>
                <button
                  className="btn primary"
                  onClick={handleSelectionConfirm}
                  disabled={selectionValues.length === 0}
                >
                  삭제하기
                </button>
                <button
                  className="btn secondary"
                  onClick={() => {
                    setSelectionContext(null);
                    setSelectionValues([]);
                    setViewMode('list');

                    setActiveMenuId(null);
                    setMenuTargetDate(null);
                  }}
                >
                  취소
                </button>
              </>
            ) : (
              <>
                <button
                  className="btn primary"
                  onClick={handleSelectionConfirm}
                >
                  선택하기
                </button>
                <button
                  className="btn secondary"
                  onClick={() => {
                    setSelectionContext(null);
                    setSelectionValues([]);
                    setViewMode('list');
                  }}
                >
                  뒤로가기
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (viewMode === 'update') {
    return (
      <div className="invite-view-wrapper">
        <div className="invite-view-panel">
          <div className="invite-content-shell invite-fade-soft" key="update">
            <UpdateEvent
              event={selectedEvent}
              eventsForDate={selectedDateEvents}
              onSave={updateEvent}
              onCancel={() => {
                if (prevViewMode === 'select-edit') {
                  setViewMode('select-edit');
                } else {
                  setSelectionContext(null);   
                  setSelectionValues([]);  
                  setViewMode('list');
                }
              }}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="invite-view-wrapper">
      <div className="invite-view-panel">
        <div className="invite-content-shell invite-fade-soft" key={viewMode}>
          <div className="invite-container" onClick={() => setActiveMenuId(null)}>

            <header className="invite-header">
              {isDeleteMode ? (
                <div className="delete-header-container">
                  <div className="delete-icon-wrapper">
                    <ExclamationIcon />
                  </div>
                  <h2 className="delete-header-title">
                    선택된 일정을<br/>삭제할까요?
                  </h2>
                </div>
              ) : (
                <>
                  <div className="invitedLogo"> <LogoIconWhite /> </div>
                  <h1>{partyName || "약속"}</h1>
                  <p>{partyName || "약속"}에 초대되었어요</p>
                  <p>약속 범위 안에서 나의 일정이예요</p>
                </>
              )}
            </header>

            <main className="main-content">
              <div className="date-selector-container">
                {candidateDates.length > 0 ? (
                  candidateDates.map((candidate, index) => {
                    const dayEvents = getEventsForDate(candidate.date);
                    const hasEvent = dayEvents.length > 0;
                    const joinedTitles = dayEvents.map(e => e.title).join(", ");

                    const isSelectedForDelete = hasEvent && allEvents.some(e => {
                        const eDate = new Date(e.start);
                        eDate.setHours(0,0,0,0);
                        const dDate = new Date(candidate.date);
                        dDate.setHours(0,0,0,0);
                        return eDate.getTime() === dDate.getTime() && selectionValues.includes(e.id);
                    });

                    return (
                      <div
                        key={index}
                        className="event-box"
                        onClick={(e) => {
                          e.stopPropagation();
                        }}
                        style={{
                          backgroundColor: hasEvent ? "#F9CBAA" : "#E9E9E3",
                          color: hasEvent ? "#FFFFFF" : "#C4C5B7",
                          cursor: isDeleteMode && hasEvent ? 'pointer' : 'default',
                          opacity: isDeleteMode && !hasEvent ? 0.5 : 1
                        }}
                      >
                        {isDeleteMode ? (
                            hasEvent && (
                                <div className="edit-icon-pos">
                              {isSelectedForDelete ? <CheckCircleIcon /> : <EmptyCircleIcon />}
                          </div>
                      )
                  ) : (
                      <button 
                        className="edit-icon-pos" 
                        onClick={(e) => toggleMenu(e, candidate.date)}
                      >
                        <EditIcon />
                      </button>
                  )}

                  <div className="event-date">{candidate.date.getDate()}</div> 
                  
                  <div className="event-info">
                    {hasEvent ? (
                      dayEvents.map((evt, i) => (
                        <span key={i} className="event-title">
                          {evt.title}
                        </span>
                      ))
                    ) : (
                      <span className="event-title">약속 없음</span>
                    )}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="empty-event-box"><div className="event-date">No Dates</div></div>
          )}
        </div>
      </main>

      {activeMenuId && menuTargetDate && !isDeleteMode && (
        <div 
          className="popup-menu" 
          style={{ 
            position: 'fixed', 
            top: `${popupPos.top}px`, 
            left: `${popupPos.left}px` 
          }}
          onClick={(e) => e.stopPropagation()} 
        >
          <button className="popup-btn add" onClick={() => handleAddClick(menuTargetDate)}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><path d="M12 5v14M5 12h14"/></svg>
            추가하기
          </button>
          
          <button className="popup-btn normal" onClick={() => handleEditClick(menuTargetDate, getEventTitleForDate(menuTargetDate))}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
            수정하기
          </button>
          
          <button className="popup-btn normal" onClick={() => enterDeleteMode(menuTargetDate)}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
            삭제하기
          </button>
        </div>
      )}

      <footer>
          <button className="confirm-btn" onClick={handleConfirm}>확인</button>
          {/* <button className="edit-btn">나의 일정 수정하기</button> */}
      </footer>
        </div>
      </div>
    </div>
    </div>
  );
};

export default Invited;