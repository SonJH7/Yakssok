import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchAllCalendarEvents } from '../api/calendar';
import WeeklyGrid from '../components/Calendar/WeeklyGrid';
import { useLayout } from '../hooks/useLayout';
import {
  addWeek,
  formatISODateTime,
  getEndOfWeek,
  getStartOfWeek,
  getWeekRangeLabel,
  subWeek,
} from '../utils/dates';
import { CalendarEvent } from '../types';

const HomeWeekly = () => {
  const navigate = useNavigate();
  const { setHeader, updateHeader } = useLayout();
  const [currentDate, setCurrentDate] = useState(() => getStartOfWeek(new Date()));
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const isLoadingRef = useRef(false);
  const isInitialLoad = useRef(true);

  const timeRange = useMemo(() => {
    const start = getStartOfWeek(currentDate);
    const end = getEndOfWeek(currentDate);
    return {
      start,
      end,
      isoStart: formatISODateTime(start),
      isoEnd: formatISODateTime(end),
    };
  }, [currentDate]);

  const loadEvents = useCallback(async () => {
    if (isLoadingRef.current) {
      return;
    }

    const initial = isInitialLoad.current;
    isLoadingRef.current = true;
    if (initial) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }
    setError('');
    updateHeader({ isRefreshing: true });

    try {      const data = await fetchAllCalendarEvents({ timeMin: timeRange.isoStart, timeMax: timeRange.isoEnd });
      setEvents(data);
    } catch (err) {
      setError('일정을 불러오는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      if (initial) {
        setLoading(false);
        isInitialLoad.current = false;
      }
      setRefreshing(false);
      updateHeader({ isRefreshing: false });
      isLoadingRef.current = false;
    }
  }, [timeRange, updateHeader]);

  const handlePrev = useCallback(() => {
    setCurrentDate((prev) => subWeek(prev));
  }, []);

  const handleNext = useCallback(() => {
    setCurrentDate((prev) => addWeek(prev));
  }, []);

  const handleToday = useCallback(() => {
    setCurrentDate(getStartOfWeek(new Date()));
  }, []);

  const handleViewChange = useCallback(
    (view: 'weekly' | 'monthly') => {
      if (view === 'monthly') {
        navigate('/home/monthly');
      }
    },
    [navigate],
  );

  useEffect(() => {
    setHeader({
      periodLabel: getWeekRangeLabel(currentDate),
      onPrev: handlePrev,
      onNext: handleNext,
      onToday: handleToday,
      viewType: 'weekly',
      onViewChange: handleViewChange,
      onRefresh: loadEvents,
      isRefreshing: refreshing,
    });
  }, [
    currentDate,
    handleNext,
    handlePrev,
    handleToday,
    handleViewChange,
    loadEvents,
    refreshing,
    setHeader,
  ]);
  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  useEffect(() => {
    const handleFocus = () => {
      void loadEvents();
    };
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        void loadEvents();
      }
    };

    window.addEventListener('focus', handleFocus);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.removeEventListener('focus', handleFocus);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [loadEvents]);

  return (
    <div className="flex h-full flex-col gap-4">
      {loading && <div className="rounded-md bg-white/70 px-4 py-2 text-sm text-ink/60">일정을 불러오는 중...</div>}
      {refreshing && !loading && !error && (
        <div className="rounded-md bg-positive/10 px-4 py-2 text-xs text-positive">최신 일정으로 동기화하는 중입니다...</div>
      )}      
      {error && <div className="rounded-md bg-warning/30 px-4 py-2 text-sm text-ink">{error}</div>}
      {!loading && events.length === 0 && !error && (
        <div className="rounded-md border border-dashed border-border px-4 py-6 text-center text-sm text-ink/60">
          이번 주 일정이 없습니다. Google 캘린더에서 일정을 추가해보세요.
        </div>
      )}
      <div className="flex-1 overflow-hidden rounded-xl border border-border/80 bg-white/60 shadow-inner">
        <WeeklyGrid events={events} start={timeRange.start} />
      </div>
    </div>
  );
};

export default HomeWeekly;
