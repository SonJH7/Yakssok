import { format } from 'date-fns';
import classNames from 'classnames';
import { CalendarEvent } from '../../types';
import { getMonthMatrix, isDateInCurrentMonth } from '../../utils/dates';
import { getEventColorClass } from '../../utils/colors';

interface MonthlyGridProps {
  events: CalendarEvent[];
  current: Date;
}

const MonthlyGrid = ({ events, current }: MonthlyGridProps) => {
  const matrix = getMonthMatrix(current);
  const eventsByDate = events.reduce<Record<string, CalendarEvent[]>>((acc, event) => {
    const dateKey = format(new Date(event.start), 'yyyy-MM-dd');
    if (!acc[dateKey]) {
      acc[dateKey] = [];
    }
    acc[dateKey].push(event);
    return acc;
  }, {});

  return (
    <div className="grid flex-1 grid-cols-7 border border-border/80 bg-white/40 text-sm">
      {matrix.flat().map((day) => {
        const dateKey = format(day, 'yyyy-MM-dd');
        const dayEvents = eventsByDate[dateKey] ?? [];
        const visibleEvents = dayEvents.slice(0, 3);
        const hiddenCount = Math.max(0, dayEvents.length - visibleEvents.length);
        return (
          <div
            key={dateKey}
            className={classNames(
              'flex h-32 flex-col border-r border-b border-border/60 p-2 transition hover:bg-positive/10',
              !isDateInCurrentMonth(day, current) && 'bg-ivory/80 text-ink/40',
            )}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold">{format(day, 'd')}</span>
            </div>
            <div className="mt-2 space-y-1 text-[11px]">
              {visibleEvents.map((event) => (
                <div key={event.id} className="flex items-center gap-2">
                  <span className={`h-2 w-2 rounded-full ${getEventColorClass(event.summary)}`} />
                  <span className="truncate">{event.summary}</span>
                </div>
              ))}
              {hiddenCount > 0 && (
                <div className="text-xs text-ink/60">+{hiddenCount} more</div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default MonthlyGrid;
