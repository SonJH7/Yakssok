import axios from 'axios';

const API_BASE_URL = 'http://localhost:7777'

export interface ReauthPayload {
  visible: boolean;
  code?: string;
  message?: string;
  reauthUrl?: string;
}

interface ConfigureClientOptions {
  getToken?: () => string;
  onUnauthorized?: () => void;
  onReauthRequired?: (payload: ReauthPayload) => void;
}

const reauthCodes = new Set([
  'google_reauth_required',
  'calendar_scope_missing',
  'insufficient_scope',
]);

const defaultHandlers = {
  getToken: () => '',
  onUnauthorized: () => {},
  onReauthRequired: (_payload: ReauthPayload) => {},
};

const handlers = { ...defaultHandlers };

export const configureClient = ({ getToken, onUnauthorized, onReauthRequired }: ConfigureClientOptions) => {
  if (getToken) handlers.getToken = getToken;
  if (onUnauthorized) handlers.onUnauthorized = onUnauthorized;
  if (onReauthRequired) handlers.onReauthRequired = onReauthRequired;
};

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

apiClient.interceptors.request.use((config) => {
  const token = handlers.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response) {
      const { status, data } = error.response;
      const code: string | undefined = data?.code;
      if (code && reauthCodes.has(code)) {
        const messageMap: Record<string, string> = {
          google_reauth_required: 'Google 인증 세션이 만료되었습니다. 다시 연결해주세요.',
          calendar_scope_missing: '캘린더 접근 권한이 부족합니다. 다시 연결해주세요.',
          insufficient_scope: '요청한 범위 권한이 없습니다. 권한을 다시 부여해주세요.',
        };
        handlers.onReauthRequired({
          visible: true,
          code,
          message: data?.message ?? messageMap[code] ?? 'Google 권한을 다시 연결해주세요.',
          reauthUrl: data?.reauthUrl,
        });
        return Promise.reject(error);
      }

      if (status === 401) {
        handlers.onUnauthorized();
      }
    }
    return Promise.reject(error);
  },
);
