import { Outlet } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";

import SidebarLeft from "./components/SidebarLeft";
import { API_BASE_URL } from "./config/api";

/* 
  좌측 사이드바 고정 레이아웃
  - 각 페이지는 <Outlet />으로 렌더링

*/

export default function AppLayout() {
  // 약속 데이터 목록 상태
  const [sidebarEvents, setSidebarEvents] = useState([]);

  // 에러 메시지 상태
  const [error, setError] = useState("");

  // 로그인 토큰
  const token = useMemo(() => localStorage.getItem("access_token"), []);

  useEffect(() => {
    const fetchAppointments = async () => {
      try {
        setError("");

        const res = await fetch(`${API_BASE_URL}/appointments/`, {
          method: "GET",
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
        });

        if (!res.ok) {
          const text = await res.text();
          throw new Error(text || `HTTP ${res.status}`);
        }

        const data = await res.json();

        const mapped = data.map((a) => ({
          id: a.id,
          name: a.name,
          invite_link: a.invite_link,
          start: null, // 날짜 데이터 없음 (260105 ver.) 이후 받아야 함
          className: `yakssok-${a.id}`,
        }));

        setSidebarEvents(mapped);
      } catch (e) {
        console.error(e);
        setError("약속 목록을 불러오지 못함.");
        setSidebarEvents([]);
      }
    };

    fetchAppointments();
  }, [token]);


  return (
    <div className="appLayout">
      <SidebarLeft events={sidebarEvents} />
      <Outlet className="content" />
    </div>
  );
}
