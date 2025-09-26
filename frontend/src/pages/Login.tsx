import { useState } from 'react';
import { requestGoogleLogin } from '../api/auth';

const Login = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const startLogin = async (force: boolean) => {
    try {
      setLoading(true);
      setError('');
      const { auth_url: authUrl } = await requestGoogleLogin(force);
      window.location.assign(authUrl);
    } catch (err) {
      setError('로그인 URL을 가져오지 못했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-ivory">
      <div className="w-full max-w-md rounded-2xl bg-white/80 p-8 shadow-xl">
        <div className="flex h-12 w-12 items-center justify-center rounded-lg border border-border">
          <div className="grid grid-cols-3 gap-0.5">
            {Array.from({ length: 9 }).map((_, index) => (
              <span key={index} className="h-1.5 w-1.5 rounded-full bg-positive" />
            ))}
          </div>
        </div>
        <h1 className="mt-6 text-2xl font-bold text-ink">할 수 있다. 일단 트라이.</h1>
        <p className="mt-2 text-sm text-ink/60">Yakssok 캘린더에 연결하여 스케줄을 확인하세요.</p>
        <div className="mt-6 space-y-3">
          <button
            type="button"
            className="w-full rounded-md bg-positive px-4 py-3 text-sm font-semibold text-white transition hover:bg-positive/90 disabled:opacity-70"
            onClick={() => startLogin(false)}
            disabled={loading}
          >
            {loading ? '연결 중...' : 'Google로 로그인'}
          </button>
          <button
            type="button"
            className="w-full rounded-md border border-border px-4 py-3 text-sm font-semibold text-ink transition hover:border-positive hover:text-positive disabled:opacity-70"
            onClick={() => startLogin(true)}
            disabled={loading}
          >
            권한 재인증(강제)
          </button>
        </div>
        {error && <div className="mt-4 text-sm text-warning">{error}</div>}
        {loading && (
          <div className="mt-4 flex items-center gap-2 text-sm text-ink/60">
            <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-positive border-t-transparent" />
            <span>Google OAuth 페이지를 여는 중입니다...</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default Login;
