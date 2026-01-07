import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Calendar from '../components/Calendar';
import SidebarRight from '../components/SidebarRight';
import './Home.css';

// const googleCalendarApiKey = process.env.REACT_APP_GOOGLE_CALENDAR_API_KEY;
// const googleCalendarId = process.env.REACT_APP_GOOGLE_CALENDAR_ID;

const Home = () => {
  const [open, setOpen] = useState(false);
  const [selectedPayload, setSelectedPayload] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('access_token');

    if (!token) {
      navigate('/', { replace: true });
      return;
    }

    const parts = token.split('.');
    if (parts.length < 2) {
      localStorage.removeItem('access_token');
      navigate('/', { replace: true });
      return;
    }

    try {
      const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
      const exp = payload?.exp;

      if (!exp || Date.now() >= exp * 1000) {
        localStorage.removeItem('access_token');
        navigate('/', { replace: true });
      }
    } catch (error) {
      console.warn('토큰 만료 여부 확인 중 문제가 발생했습니다.', error);
      localStorage.removeItem('access_token');
      navigate('/', { replace: true });
    }
  }, [navigate]);

  return (
    <div className="home-container">
      {/* Header */}
      <header className="home-header"></header>

      {/* 캘린더 영역 */}
      <main className="main-content">
        <Calendar
          onEventSelect={(payload) => {
            setSelectedPayload(payload);
            setOpen(true);
          }}
        />
      </main>

      <SidebarRight 
        open={open} 
        onClose={() => setOpen(false)} 
        selectedPayload={selectedPayload}
      />
      
    </div>
  );
};

export default Home;