export interface CalendarDateTime {
  date?: string;
  dateTime?: string;
  timeZone?: string;
}

export interface CalendarEvent {
  id: string;
  summary: string;
  start: string | CalendarDateTime;
  end: string | CalendarDateTime;
  location?: string;
}

export interface CalendarEventResponse {
  events: CalendarEvent[];
  nextPageToken?: string;
}
