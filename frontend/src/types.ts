export interface CalendarEvent {
  id: string;
  summary: string;
  start: string;
  end: string;
  location?: string;
}

export interface CalendarEventResponse {
  events: CalendarEvent[];
  nextPageToken?: string;
}
