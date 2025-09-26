import { apiClient } from './client';

interface LoginResponse {
  auth_url: string;
}

export const requestGoogleLogin = async (force = false) => {
  const response = await apiClient.get<LoginResponse>(`/user/google/login${force ? '?force=1' : ''}`);
  return response.data;
};
