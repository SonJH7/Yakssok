import { format } from 'date-fns';
import { CalendarEvent } from '../../types';
import { getEventColorClass } from '../../utils/colors';

interface EventItemProps {
  event: CalendarEvent;
  className?: string;
  style?: React.CSSProperties;
  showTime?: boolean;
}

const EventItem = ({ event, className, style, showTime = true }: EventItemProps) => {
  const startDate = new Date(event.start);
  const endDate = new Date(event.end);
  const timeLabel = `${format(startDate, 'HH:mm')} - ${format(endDate, 'HH:mm')}`;
  const colorClass = getEventColorClass(event.summary);

  return (
    <div
      className={`group relative rounded-md border border-white/70 px-2 py-1 text-xs text-ink shadow-sm transition hover:shadow-md ${colorClass} ${className ?? ''}`.trim()}
      style={style}
    >
      <div className="font-semibold">{event.summary || '제목 없음'}</div>
      {showTime && <div className="text-[10px] text-ink/80">{timeLabel}</div>}
      {event.location && <div className="mt-0.5 text-[10px] text-ink/60">{event.location}</div>}
    </div>
  );
};

export default EventItem;
