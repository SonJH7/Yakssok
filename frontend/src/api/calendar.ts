import { apiClient } from './client';
import { CalendarEvent, CalendarEventResponse } from '../types';

interface FetchCalendarParams {
  timeMin: string;
  timeMax: string;
  maxResults?: number;
}

export const fetchCalendarEvents = async (
  params: FetchCalendarParams & { pageToken?: string },
): Promise<CalendarEventResponse> => {
  const response = await apiClient.get<CalendarEventResponse>('/calendar/events', {
    params: {
      time_min: params.timeMin,
      time_max: params.timeMax,
      max_results: params.maxResults ?? 50,
      page_token: params.pageToken,
    },
  });
  return response.data;
};

export const fetchAllCalendarEvents = async (params: FetchCalendarParams): Promise<CalendarEvent[]> => {
  const events: CalendarEvent[] = [];
  let pageToken: string | undefined;

  do {
    const response = await fetchCalendarEvents({ ...params, pageToken });
    events.push(...response.events);
    pageToken = response.nextPageToken;
  } while (pageToken);

  return events;
};
