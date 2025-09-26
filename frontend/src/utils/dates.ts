import {
  addMonths,
  addWeeks,
  eachDayOfInterval,
  endOfMonth,
  endOfWeek,
  format,
  formatISO,
  getDaysInMonth,
  isSameMonth,
  startOfMonth,
  startOfWeek,
  subMonths,
  subWeeks,
} from 'date-fns';
import { ko } from 'date-fns/locale';

export const getStartOfWeek = (date: Date) => startOfWeek(date, { weekStartsOn: 1 });
export const getEndOfWeek = (date: Date) => endOfWeek(date, { weekStartsOn: 1 });

export const getStartOfMonth = (date: Date) => startOfMonth(date);
export const getEndOfMonth = (date: Date) => endOfMonth(date);

export const getWeekRangeLabel = (date: Date) => {
  const start = getStartOfWeek(date);
  const end = getEndOfWeek(date);
  return `${format(start, 'yyyy년 M월 d일', { locale: ko })} – ${format(end, 'M월 d일', { locale: ko })}`;
};

export const getMonthLabel = (date: Date) => format(date, 'yyyy년 M월', { locale: ko });

export const getWeekDays = (date: Date) => {
  const start = getStartOfWeek(date);
  const end = getEndOfWeek(date);
  return eachDayOfInterval({ start, end });
};

export const addWeek = (date: Date) => addWeeks(date, 1);
export const subWeek = (date: Date) => subWeeks(date, 1);
export const addMonth = (date: Date) => addMonths(date, 1);
export const subMonth = (date: Date) => subMonths(date, 1);

export const formatISODateTime = (date: Date) => formatISO(date);

export const getMonthMatrix = (date: Date) => {
  const start = getStartOfWeek(startOfMonth(date));
  const end = getEndOfWeek(endOfMonth(date));
  const days = eachDayOfInterval({ start, end });
  const weeks: Date[][] = [];

  for (let i = 0; i < days.length; i += 7) {
    weeks.push(days.slice(i, i + 7));
  }

  return weeks;
};

export const isDateInCurrentMonth = (date: Date, current: Date) => isSameMonth(date, current);

export const getDaysCountOfMonth = (date: Date) => getDaysInMonth(date);

export const toValidDate = (value: string | Date | null | undefined) => {
  if (!value) {
    return null;
  }

  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
};