const TOKEN_KEY = 'access_token';

export const getStoredToken = () => {
  return localStorage.getItem(TOKEN_KEY) ?? '';
};

export const storeToken = (token: string) => {
  localStorage.setItem(TOKEN_KEY, token);
};

export const clearToken = () => {
  localStorage.removeItem(TOKEN_KEY);
};

export default {
  getStoredToken,
  storeToken,
  clearToken,
};
