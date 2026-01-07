import React, { useState, useEffect } from 'react';
import './EventPage.css'; 

const QuestionIcon = () => (
  <svg width="42" height="42" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="12" r="12" fill="#74ABB4"/>
    <path d="M9.09 9C9.3251 8.33167 9.78915 7.76811 10.4 7.40913C11.0108 7.05016 11.7289 6.91894 12.4272 7.03871C13.1255 7.15849 13.7588 7.52152 14.2151 8.06353C14.6713 8.60553 14.9211 9.29152 14.92 10C14.92 12 11.92 13 11.92 13" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M12 17H12.01" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const DateCheckIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="12" r="12" fill="#BBCEA0"/>
    <path d="M16 9L10.5 14.5L8 12" stroke="#FAFFF2" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const UpdateEvent = ({ event, eventsForDate = [], onSave, onCancel }) => {
  const [title, setTitle] = useState('');
  const [startTime, setStartTime] = useState('');
  const [endTime, setEndTime] = useState('');

  const [initialTitle, setInitialTitle] = useState('');
  const [initialStartTime, setInitialStartTime] = useState('');
  const [initialEndTime, setInitialEndTime] = useState('');

  const formatTime = (dateObj) => {
    if (!dateObj) return '';
    const hh = String(dateObj.getHours()).padStart(2, '0');
    const mm = String(dateObj.getMinutes()).padStart(2, '0');
    return `${hh}:${mm}`;
  };

  useEffect(() => {
  if (!event) return;

  const sDate = new Date(event.start);
  const sTime = formatTime(sDate);

  let eTime;
  if (event.end) {
    eTime = formatTime(new Date(event.end));
  } else {
    const eDate = new Date(sDate.getTime() + 60 * 60 * 1000);
    eTime = formatTime(eDate);
  }

  setTitle(event.title);
  setStartTime(sTime);
  setEndTime(eTime);

  setInitialTitle(event.title);
  setInitialStartTime(sTime);
  setInitialEndTime(eTime);
}, [event]);

  const hasAnyInput =
  title.trim() !== initialTitle ||
  startTime !== initialStartTime ||
  endTime !== initialEndTime

  const handleSave = () => {
    if (!hasAnyInput) {
      return;
    }

    const updatedEvent = { ...event };
    const updatePayload = {};

    if (title.trim()) {
      const trimmed = title.trim();
      updatedEvent.title = trimmed;
      updatePayload.summary = trimmed;
    }

    const hasBothTimes = Boolean(startTime && endTime);

    if (startTime || endTime) {
      if (!hasBothTimes) {
        alert('시작 시간과 종료 시간을 모두 입력해주세요.');
        return;
      }

      const baseDate = new Date(event.start);
      const year = baseDate.getFullYear();
      const month = baseDate.getMonth();
      const day = baseDate.getDate();

      const [startH, startM] = startTime.split(':').map(Number);
      const newStartDate = new Date(year, month, day, startH, startM);

      const [endH, endM] = endTime.split(':').map(Number);
      const newEndDate = new Date(year, month, day, endH, endM);

      if (newEndDate < newStartDate) {
        alert("종료 시간이 시작 시간보다 빠를 수 없습니다.");
        return;
      }

      updatedEvent.start = newStartDate;
      updatedEvent.end = newEndDate;
      updatePayload.start = {
        dateTime: newStartDate.toISOString(),
        timeZone: 'Asia/Seoul',
      };
      updatePayload.end = {
        dateTime: newEndDate.toISOString(),
        timeZone: 'Asia/Seoul',
      };
    }

    onSave(updatedEvent, updatePayload);
  };

  const displayDate = event ? new Date(event.start) : null;
  const selectedId = event?.id;
  const sourceEvents = eventsForDate.length > 0 ? eventsForDate : event ? [event] : [];
  const orderedEvents = selectedId
    ? [
        ...sourceEvents.filter((evt) => evt.id === selectedId),
        ...sourceEvents.filter((evt) => evt.id !== selectedId),
      ]
    : sourceEvents;

  const isMultiEdit = orderedEvents.length > 1;

  return (
    <div className="event-page-overlay">
      <div className="event-page-container">
        
        <div className="create-header-wrapper">
          <div className="header-icon">
            <QuestionIcon />
          </div>
          <h2 className="header-title-text">
            선택된 일정에서<br />무엇을 수정할까요?
          </h2>
        </div>

        <div 
          className="selected-date-box"
          style={{ backgroundColor: '#F9CBAA' }} 
        >
          <div 
            className="selected-date-num"
            style={{ color: '#FFFFFF' }} 
          >
            {displayDate ? displayDate.getDate() : "0"}
          </div>
          <div className="date-check-icon">
            <DateCheckIcon />
          </div>
          <div className="selected-event-title-list" style={{ color: '#FFFFFF' }}>
            {orderedEvents.map((evt) => {
              const title = evt?.title || evt?.summary || '제목 없음';
              const isSelected = evt?.id === selectedId;
              return (
                <span
                  key={evt.id || title}

                  className={`selected-event-title${isSelected && isMultiEdit ? ' selected-event-title--active' : ''}`}

                >
                  {title}
                </span>
              );
            })}
          </div>
        </div>

        <div className="input-group">
          <label>약속 이름</label>
          <input 
            type="text" 
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="약속 이름을 입력하세요"
          />
        </div>

        <div className="input-group">
          <label>약속 시간</label>
          <div className="time-range-wrapper">
            <input 
              type="time" 
              className="time-input"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              onClick={(e) => e.target.showPicker?.()}
            />
            <span className="time-separator">~</span>
            <input 
              type="time" 
              className="time-input"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              onClick={(e) => e.target.showPicker?.()}
            />
          </div>
        </div>

        <div className="button-group">
          <button
            className="btn primary"
            onClick={handleSave}
            disabled={!hasAnyInput}
          >
            수정하기
          </button>
          <button className="btn secondary" onClick={onCancel}>뒤로가기</button>
        </div>
      </div>
    </div>
  );
};

export default UpdateEvent;