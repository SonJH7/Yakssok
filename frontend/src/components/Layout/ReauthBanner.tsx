interface ReauthBannerProps {
  visible: boolean;
  message?: string;
  loading?: boolean;
  onReauth: () => void;
  onClose: () => void;
}

const ReauthBanner = ({ visible, message, loading, onReauth, onClose }: ReauthBannerProps) => {
  if (!visible) {
    return null;
  }

  return (
    <div className="flex items-center justify-between border-b border-warning/40 bg-warning/30 px-6 py-2 text-sm text-ink">
      <div>{message ?? 'Google 권한이 만료되었습니다. 다시 연결해주세요.'}</div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="rounded-md border border-warning px-3 py-1 text-sm font-medium text-ink transition hover:bg-warning/40"
          onClick={onReauth}
          disabled={loading}
        >
          {loading ? '연결 중...' : 'Google 권한 다시 연결'}
        </button>
        <button
          type="button"
          className="rounded-md border border-border px-2 py-1 text-xs text-ink/60 transition hover:text-ink"
          onClick={onClose}
        >
          닫기
        </button>
      </div>
    </div>
  );
};

export default ReauthBanner;
