import {
  addHours,
  differenceInMinutes,
  format,
  setHours,
  setMinutes,
  setSeconds,
} from 'date-fns';
import { CalendarEvent } from '../../types';
import { getWeekDays, toValidDate } from '../../utils/dates';
import EventItem from './EventItem';

interface WeeklyGridProps {
  events: CalendarEvent[];
  start: Date;
}

interface PositionedEvent {
  event: CalendarEvent;
  top: number;
  height: number;
  left: string;
  width: string;
}

const START_HOUR = 8;
const END_HOUR = 22;
const PIXELS_PER_MINUTE = 64 / 60;

const resetToDayStart = (date: Date) => {
  return setSeconds(setMinutes(setHours(date, START_HOUR), 0), 0);
};

const clampToDayRange = (date: Date, day: Date) => {
  const dayStart = resetToDayStart(day);
  const dayEnd = setSeconds(setMinutes(setHours(day, END_HOUR), 0), 0);
  const start = date < dayStart ? dayStart : date;
  return start > dayEnd ? dayEnd : start;
};

const getPositionedEvents = (events: CalendarEvent[], day: Date): PositionedEvent[] => {
  const dayStart = resetToDayStart(day);
  const dayEnd = setSeconds(setMinutes(setHours(day, END_HOUR), 0), 0);

  const filtered = events
    .map((event) => {
      const rawStart = toValidDate(event.start);
      const rawEnd = toValidDate(event.end);
      if (!rawStart || !rawEnd) {
        return null;
      }
      const start = clampToDayRange(rawStart, day);
      const end = clampToDayRange(rawEnd, day);
      if (end <= dayStart || start >= dayEnd) {
        return null;
      }
      return {
        event,
        start,
        end,
        startMinutes: Math.max(0, differenceInMinutes(start, dayStart)),
        endMinutes: Math.max(0, differenceInMinutes(end, dayStart)),
      };
    })
    .filter((value): value is {
      event: CalendarEvent;
      start: Date;
      end: Date;
      startMinutes: number;
      endMinutes: number;
    } => Boolean(value))
    .sort((a, b) => a.start.getTime() - b.start.getTime());

  const positioned: PositionedEvent[] = [];
  const active: Array<{ startMinutes: number; endMinutes: number; col: number; node: PositionedEvent }> = [];

  const updateActiveWidths = () => {
    if (active.length === 0) {
      return;
    }
    const maxCol = Math.max(...active.map((item) => item.col)) + 1;
    const width = 100 / maxCol;
    active.forEach((activeItem) => {
      activeItem.node.width = `calc(${width}% - 6px)`;
      activeItem.node.left = `calc(${(100 / maxCol) * activeItem.col}% + ${activeItem.col * 4}px)`;
    });
  };

  filtered.forEach((item) => {
    const { startMinutes, endMinutes } = item;
    for (let i = active.length - 1; i >= 0; i -= 1) {
      if (active[i].endMinutes <= startMinutes) {
        active.splice(i, 1);
      }
    }
    updateActiveWidths();

    const usedColumns = new Set(active.map((a) => a.col));
    let col = 0;
    while (usedColumns.has(col)) {
      col += 1;
    }

    const top = startMinutes * PIXELS_PER_MINUTE;
    const height = Math.max(36, (endMinutes - startMinutes) * PIXELS_PER_MINUTE);
    const position: PositionedEvent = {
      event: item.event,
      top,
      height,
      left: '0%',
      width: '100%',
    };

    const node = { startMinutes, endMinutes, col, node: position };
    active.push(node);
    updateActiveWidths();

    positioned.push(position);
  });

  return positioned;
};

const WeeklyGrid = ({ events, start }: WeeklyGridProps) => {
  const days = getWeekDays(start);
  const hours = Array.from({ length: END_HOUR - START_HOUR + 1 }, (_, index) => START_HOUR + index);

  return (
    <div className="flex h-full flex-col">
      <div className="grid grid-cols-8 border-b border-border/80 bg-white/60 text-sm text-ink">
        <div className="px-2 py-3 text-right text-xs text-ink/60">시간</div>
        {days.map((day) => (
          <div key={day.toISOString()} className="px-2 py-3 text-center">
            <div className="text-xs text-ink/60">{format(day, 'EEE')}</div>
            <div className="text-base font-semibold">{format(day, 'd')}</div>
          </div>
        ))}
      </div>
      <div className="flex flex-1 overflow-hidden">
        <div className="relative w-16 border-r border-border/80 bg-white/40 text-right text-xs text-ink/60">
          {hours.map((hour) => (
            <div key={hour} className="h-16 border-b border-border/60 pr-2">
              <span className="relative -top-2 inline-block">{`${hour.toString().padStart(2, '0')}:00`}</span>
            </div>
          ))}
        </div>
        <div className="relative flex-1">
          <div className="absolute inset-0 grid grid-cols-7">
            {days.map((day) => {
              const dayEvents = events.filter((event) => {
                const eventStart = toValidDate(event.start);
                const eventEnd = toValidDate(event.end);
                if (!eventStart || !eventEnd) {
                  return false;
                }

                return eventEnd > day && eventStart < addHours(day, 24);
              });
              const positioned = getPositionedEvents(dayEvents, day);
              return (
                <div key={day.toISOString()} className="relative border-r border-border/60 last:border-r-0">
                  {hours.map((hour) => (
                    <div key={hour} className="h-16 border-b border-border/40" />
                  ))}
                  {positioned.map((item) => (
                    <EventItem
                      key={`${item.event.id}-${item.top}`}
                      event={item.event}
                      style={{
                        position: 'absolute',
                        top: item.top,
                        height: item.height,
                        left: item.left,
                        width: item.width,
                      }}
                    />
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeeklyGrid;
