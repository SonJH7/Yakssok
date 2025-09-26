import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { configureClient, ReauthPayload } from '../api/client';
import { clearToken as clearStoredToken, getStoredToken, storeToken } from '../utils/storage';

interface AuthContextValue {
  token: string;
  initializing: boolean;
  setToken: (value: string) => void;
  logout: () => void;
  reauthInfo: ReauthPayload | null;
  dismissReauth: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [token, setTokenState] = useState('');
  const [initializing, setInitializing] = useState(true);
  const [reauthInfo, setReauthInfo] = useState<ReauthPayload | null>(null);
  const tokenRef = useRef(token);

  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  useEffect(() => {
    const stored = getStoredToken();
    if (stored) {
      setTokenState(stored);
    }
    setInitializing(false);
  }, []);

  const persistToken = useCallback((value: string) => {
    if (value) {
      storeToken(value);
    } else {
      clearStoredToken();
    }
  }, []);

  const setToken = useCallback(
    (value: string) => {
      setTokenState(value);
      persistToken(value);
    },
    [persistToken],
  );

  const logout = useCallback(() => {
    setToken('');
    setReauthInfo(null);
    clearStoredToken();
    window.location.replace('/login');
  }, [setToken]);

  const dismissReauth = useCallback(() => {
    setReauthInfo(null);
  }, []);

  useEffect(() => {
    configureClient({
      getToken: () => tokenRef.current,
      onUnauthorized: () => {
        logout();
      },
      onReauthRequired: (payload) => {
        setReauthInfo(payload);
      },
    });
  }, [logout]);

  const value = useMemo(
    () => ({ token, initializing, setToken, logout, reauthInfo, dismissReauth }),
    [token, initializing, setToken, logout, reauthInfo, dismissReauth],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuthContext = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('AuthContext가 설정되지 않았습니다.');
  }
  return context;
};
