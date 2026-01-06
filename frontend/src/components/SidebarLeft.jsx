import { useState, useMemo } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "./SidebarLeft.css";

import LogoIcon from "../assets/LogoIcon";
import OpenButton from "../assets/OpenButton";
import CloseButton from "../assets/CloseButton";
import NewButton from "../assets/NewButton";
import NewButtonClosed from "../assets/NewButtonClosed";
import CalendarIcon from "../assets/CalendarIcon";
import ListIcon from "../assets/ListIcon";
import CalendarIconSelected from "../assets/CalendarIconSelected";
import ListIconSelected from "../assets/ListIconSelected";
import ListDot from "../assets/ListDot";

/* 
  좌측 사이드바
  - 약속 생성 버튼
  - 약속 달력, 리스트 표시

*/

const SidebarLeft = ({ events = [] }) => {
  const navigate = useNavigate();
  const location = useLocation();

  // 사이드바 상태
  const [isOpen, setIsOpen] = useState(false);

  // 페이지 상태
  const isHomePage = location.pathname === "/home";
  const isCreatePage = location.pathname === "/create";
  const isListPage = location.pathname === "/list";

  // 로고 상태
  const [isLogoHovered, setIsLogoHovered] = useState(false);

  // 약속 생성 버튼 클릭 로직
  const handleNewButtonClick = () => {
    if (isCreatePage && !isOpen) {
      navigate("/home");
      return;
    }
    if (isCreatePage && isOpen) {
      navigate(0); // create 페이지 새로고침
      return;
    }
    navigate("/create");
  };

  // 날짜 상태
  const today = new Date();
  const todayStr = today.toLocaleDateString("sv-SE");

  const [currentMonth, setCurrentMonth] = useState(today.getMonth());
  const [currentYear, setCurrentYear] = useState(today.getFullYear());

  // 날짜 문자열 변환
  const toDateStr = (start) => {
    if (!start) return "";
    const raw =
      typeof start === "string" ? start : start?.dateTime ?? start?.date ?? "";
    return raw ? String(raw).slice(0, 10) : "";
  };

  // 약속 데이터 관리 (리스트, 달력)
  const appointmentsList = useMemo(
    () =>
      events.map((e, idx) => ({
        id: e.id ?? idx + 1,
        text: e.name ?? "(이름 없음)",
        date: toDateStr(e.start),
        invite_link: e.invite_link,
      })),
    [events]
  );

  const appointmentsCalendar = useMemo(() => {
    return appointmentsList
      .filter((a) => {
        if (!a.date) return false;
        const date = new Date(a.date);
        return (
          date.getFullYear() === currentYear && date.getMonth() === currentMonth
        );
      })
      .sort((a, b) => {
        if (a.date < todayStr && b.date >= todayStr) return 1;
        if (a.date >= todayStr && b.date < todayStr) return -1;
        return a.date.localeCompare(b.date);
      });
  }, [appointmentsList, currentYear, currentMonth, todayStr]);

  // 약속이 있는 날짜 set
  const appointmentsDateSet = useMemo(() => {
    return new Set(appointmentsCalendar.map((a) => a.date));
  }, [appointmentsCalendar]);

  // 달력 렌더링
  const renderCalendar = () => {
    const days = [];
    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

    // 앞쪽 빈 칸
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} className="empty" />);
    }

    // 날짜
    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${currentYear}-${String(currentMonth + 1).padStart(
        2,
        "0"
      )}-${String(d).padStart(2, "0")}`;

      const hasAppointment = appointmentsDateSet.has(dateStr);
      const dayOfWeek = new Date(currentYear, currentMonth, d).getDay();

      let className = "day";
      if (dayOfWeek === 0) className += " sunday";
      if (dayOfWeek === 6) className += " saturday";
      if (hasAppointment) className += " hasAppointment";

      days.push(
        <div key={d} className={className}>
          {d}
        </div>
      );
    }

    return days;
  };

  // 달력 이동 (월, 오늘)
  const moveMonth = (direction) => {
    setCurrentMonth((prev) => {
      if (direction === -1 && prev === 0) {
        setCurrentYear((y) => y - 1);
        return 11;
      }
      if (direction === 1 && prev === 11) {
        setCurrentYear((y) => y + 1);
        return 0;
      }
      return prev + direction;
    });
  };

  const handleGoToday = () => {
    setCurrentMonth(today.getMonth());
    setCurrentYear(today.getFullYear());
  };

  const daysOfWeek = ["일", "월", "화", "수", "목", "금", "토"];

  return (
    <div className={`sidebarLeft ${isOpen ? "open" : "closed"}`}>
        {/* 로고 + 열고 닫는 버튼 */}
        <div
          className={`sidebarLeftLogo ${isOpen ? "open" : ""} ${
            isLogoHovered ? "hovered" : ""
          }`}
          onMouseEnter={() => setIsLogoHovered(true)}
          onMouseLeave={() => setIsLogoHovered(false)}
        >
          <button
            className="sidebarButton openBtn"
            onClick={() => setIsOpen(true)}
          >
            <OpenButton />
          </button>

          <button
            className="sidebarButton closeBtn"
            onClick={() => setIsOpen(false)}
          >
            <CloseButton />
          </button>

          <LogoIcon className="logoIcon" />
        </div>

        {/* 새로운 약속 생성 버튼 */}
        <button className="newButton" onClick={handleNewButtonClick}>
          {isOpen ? (
            <div className="buttonIcon">
              <NewButton />
            </div>
          ) : (
            <div
              className={`buttonIconClosed ${isCreatePage ? "Rotated" : ""}`}
            >
              <NewButtonClosed />
            </div>
          )}
          {isOpen && <div className="buttonText">새로운 약속 만들기</div>}
        </button>

        {/* 페이지 이동 버튼 (닫힌 상태에서만 렌더) */}
        {!isOpen && (
          <div className="iconRow">
            <button className="iconButton" onClick={() => navigate("/home")}>
              {isHomePage ? <CalendarIconSelected /> : <CalendarIcon />}
              <span className="iconText">약속 달력</span>
            </button>

            <button
              className="iconButton" /* onClick={() => navigate("/list")} */
            >
              {isListPage ? <ListIconSelected /> : <ListIcon />}
              <span className="iconText">약속 목록</span>
            </button>
          </div>
        )}

        {/* 약속 달력 (열린 상태에서만 렌더) */}
        {isOpen && (
          <div className="calendar">
            <div className="calendarHeader">
              <button className="moveMonth" onClick={() => moveMonth(-1)}>
                {"<"}
              </button>
              <span>{currentMonth + 1}월</span>
              <button className="moveMonth" onClick={() => moveMonth(1)}>
                {">"}
              </button>
              <button className="todayButton" onClick={handleGoToday}>
                오늘
              </button>
            </div>

            {/* 요일 */}
            <div className="calendarGrid daysofWeek">
              {daysOfWeek.map((day, index) => (
                <div
                  key={day}
                  className={`dayName ${index === 0 ? "sunday" : ""} ${
                    index === 6 ? "saturday" : ""
                  }`}
                >
                  {day}
                </div>
              ))}
            </div>

            {/* 날짜 */}
            <div className="calendarGrid">{renderCalendar()}</div>
          </div>
        )}

        {/* 약속 목록 (열린 상태에서만 렌더) */}
        {isOpen && (
          <div className="appointments">
            <div className="appointmentsBox">
              <ul>
                {appointmentsList.map((a) => (
                  <li
                    key={a.id}
                    className="appointmentItem"
                    onClick={() =>
                      a.invite_link && navigate(`/result/${a.invite_link}`)
                    }
                  >
                    <ListDot />
                    <span className="appointmentText">{a.text}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* 프로필 */}
        <div className="profile" />
      </div>
  );
};

export default SidebarLeft;
