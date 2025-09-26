import { ReactNode, createContext, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { requestGoogleLogin } from '../../api/auth';
import { useAuth } from '../../hooks/useAuth';
import ReauthBanner from './ReauthBanner';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export type ViewType = 'weekly' | 'monthly';

export interface HeaderConfig {
  periodLabel: string;
  onPrev?: () => void;
  onNext?: () => void;
  onToday?: () => void;
  viewType: ViewType;
  onViewChange?: (view: ViewType) => void;
  onRefresh?: () => void | Promise<void>;
  isRefreshing?: boolean;
}

interface LayoutContextValue {
  setHeaderConfig: (config: Partial<HeaderConfig>) => void;
}

export const LayoutConfigContext = createContext<LayoutContextValue>({
  setHeaderConfig: () => {},
});

interface LayoutProps {
  children: ReactNode;
}

const defaultHeader: HeaderConfig = {
  periodLabel: '',
  viewType: 'weekly',
  isRefreshing: false,
};

const infoPanelContent = [
  '1) 사용자가 "Google로 로그인" 버튼을 클릭합니다.',
  '2) 백엔드가 Google OAuth 동의 화면 URL을 반환하고, 사용자는 해당 URL로 이동합니다.',
  '3) 동의를 완료하면 백엔드가 JWT를 발급하고 프런트엔드 콜백 URL로 토큰을 전달합니다.',
  '4) 프런트엔드는 토큰을 저장하고 모든 캘린더 API 호출에 Authorization 헤더를 포함합니다.',
];

const Layout = ({ children }: LayoutProps) => {
  const location = useLocation();
  const { logout, reauthInfo, dismissReauth } = useAuth();
  const [headerConfig, setHeaderConfig] = useState<HeaderConfig>(defaultHeader);
  const [infoOpen, setInfoOpen] = useState(false);
  const [reauthLoading, setReauthLoading] = useState(false);

  const handleReauth = async () => {
    try {
      setReauthLoading(true);
      const { auth_url: authUrl } = await requestGoogleLogin(true);
      window.location.assign(authUrl);
    } catch (error) {
      console.error(error);
      alert('재인증 링크를 가져오지 못했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setReauthLoading(false);
    }
  };

  const contextValue = useMemo(
    () => ({
      setHeaderConfig: (config: Partial<HeaderConfig>) => {
        setHeaderConfig((prev) => ({ ...prev, ...config }));
      },
    }),
    [],
  );

  return (
    <LayoutConfigContext.Provider value={contextValue}>
      <div className="flex h-screen bg-ivory">
        <Sidebar currentPath={location.pathname} onToggleInfo={() => setInfoOpen((prev) => !prev)} />
        <div className="relative flex flex-1 flex-col">
          <ReauthBanner
            visible={Boolean(reauthInfo?.visible)}
            message={reauthInfo?.message}
            loading={reauthLoading}
            onClose={dismissReauth}
            onReauth={handleReauth}
          />
          <TopBar
            periodLabel={headerConfig.periodLabel}
            onPrev={headerConfig.onPrev}
            onNext={headerConfig.onNext}
            onToday={headerConfig.onToday}
            viewType={headerConfig.viewType}
            onViewChange={headerConfig.onViewChange}
            onRefresh={headerConfig.onRefresh}
            isRefreshing={headerConfig.isRefreshing}
            onToggleInfo={() => setInfoOpen((prev) => !prev)}
            onLogout={logout}
          />
          <div className="relative flex flex-1 overflow-hidden">
            <main className="flex-1 overflow-y-auto p-6 pr-4">{children}</main>
            <aside
              className={`absolute right-0 top-0 h-full w-72 transform bg-white/90 p-6 shadow-lg transition-transform duration-300 ease-in-out ${infoOpen ? 'translate-x-0' : 'translate-x-full'}`}
              aria-hidden={!infoOpen}
            >
              <h2 className="text-lg font-semibold text-ink">OAuth 흐름 안내</h2>
              <ol className="mt-4 space-y-3 text-sm text-ink/70">
                {infoPanelContent.map((item) => (
                  <li key={item} className="flex gap-2">
                    <span className="mt-1 h-2 w-2 flex-shrink-0 rounded-full bg-positive" />
                    <span>{item}</span>
                  </li>
                ))}
              </ol>
              <button
                type="button"
                className="mt-6 w-full rounded-md border border-border px-4 py-2 text-sm text-ink transition hover:border-positive hover:text-positive"
                onClick={() => setInfoOpen(false)}
              >
                닫기
              </button>
            </aside>
          </div>
        </div>
      </div>
    </LayoutConfigContext.Provider>
  );
};

export default Layout;
