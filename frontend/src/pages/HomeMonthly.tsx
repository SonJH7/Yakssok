import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchAllCalendarEvents } from '../api/calendar';
import MonthlyGrid from '../components/Calendar/MonthlyGrid';
import { useLayout } from '../hooks/useLayout';
import {
  addMonth,
  formatISODateTime,
  getEndOfMonth,
  getMonthLabel,
  getStartOfMonth,
  subMonth,
} from '../utils/dates';
import { CalendarEvent } from '../types';

const HomeMonthly = () => {
  const navigate = useNavigate();
  const { setHeader } = useLayout();
  const [currentDate, setCurrentDate] = useState(() => getStartOfMonth(new Date()));
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const range = useMemo(() => {
    const start = getStartOfMonth(currentDate);
    const end = getEndOfMonth(currentDate);
    return {
      start,
      end,
      isoStart: formatISODateTime(start),
      isoEnd: formatISODateTime(end),
    };
  }, [currentDate]);

  const loadEvents = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const data = await fetchAllCalendarEvents({ timeMin: range.isoStart, timeMax: range.isoEnd });
      setEvents(data);
    } catch (err) {
      setError('일정을 불러오는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  }, [range]);

  const handlePrev = useCallback(() => {
    setCurrentDate((prev) => subMonth(prev));
  }, []);

  const handleNext = useCallback(() => {
    setCurrentDate((prev) => addMonth(prev));
  }, []);

  const handleToday = useCallback(() => {
    setCurrentDate(getStartOfMonth(new Date()));
  }, []);

  const handleViewChange = useCallback(
    (view: 'weekly' | 'monthly') => {
      if (view === 'weekly') {
        navigate('/home/weekly');
      }
    },
    [navigate],
  );

  useEffect(() => {
    setHeader({
      periodLabel: getMonthLabel(currentDate),
      onPrev: handlePrev,
      onNext: handleNext,
      onToday: handleToday,
      viewType: 'monthly',
      onViewChange: handleViewChange,
    });
  }, [currentDate, handleNext, handlePrev, handleToday, handleViewChange, setHeader]);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  return (
    <div className="flex h-full flex-col gap-4">
      {loading && <div className="rounded-md bg-white/70 px-4 py-2 text-sm text-ink/60">일정을 불러오는 중...</div>}
      {error && <div className="rounded-md bg-warning/30 px-4 py-2 text-sm text-ink">{error}</div>}
      {!loading && events.length === 0 && !error && (
        <div className="rounded-md border border-dashed border-border px-4 py-6 text-center text-sm text-ink/60">
          이번 달 일정이 없습니다. Google 캘린더에서 일정을 추가해보세요.
        </div>
      )}
      <div className="flex-1 overflow-hidden rounded-xl border border-border/80 bg-white/60 shadow-inner">
        <MonthlyGrid events={events} current={range.start} />
      </div>
    </div>
  );
};

export default HomeMonthly;
