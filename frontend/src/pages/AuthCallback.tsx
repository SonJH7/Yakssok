import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const AuthCallback = () => {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { setToken } = useAuth();
  const [error, setError] = useState('');

  useEffect(() => {
    const accessToken = params.get('access_token');
    if (!accessToken) {
      setError('토큰이 존재하지 않습니다. 다시 로그인해주세요.');
      return;
    }

    // 데모 목적상 localStorage에 저장합니다. 운영 환경에서는 httpOnly 쿠키 사용을 권장합니다.
    setToken(accessToken);
    navigate('/home/weekly', { replace: true });
  }, [navigate, params, setToken]);

  if (error) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-ivory text-ink">
        <div className="rounded-xl bg-white/80 p-8 text-center shadow-lg">
          <h2 className="text-lg font-semibold">인증 오류</h2>
          <p className="mt-2 text-sm text-ink/60">{error}</p>
          <button
            type="button"
            className="mt-4 rounded-md border border-border px-4 py-2 text-sm text-ink transition hover:border-positive hover:text-positive"
            onClick={() => navigate('/login', { replace: true })}
          >
            로그인 페이지로 이동
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ivory text-ink">
      <div className="rounded-xl bg-white/80 px-6 py-4 text-sm shadow-lg">
        Google 인증 정보를 확인 중입니다...
      </div>
    </div>
  );
};

export default AuthCallback;
