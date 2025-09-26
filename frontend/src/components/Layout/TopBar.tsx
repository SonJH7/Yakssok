import classNames from 'classnames';
import { ViewType } from './Layout';

interface TopBarProps {
  periodLabel: string;
  onPrev?: () => void;
  onNext?: () => void;
  onToday?: () => void;
  viewType: ViewType;
  onViewChange?: (view: ViewType) => void;
  onToggleInfo: () => void;
  onLogout: () => void;
}

const TopBar = ({
  periodLabel,
  onPrev,
  onNext,
  onToday,
  viewType,
  onViewChange,
  onToggleInfo,
  onLogout,
}: TopBarProps) => {
  const views: ViewType[] = ['weekly', 'monthly'];

  return (
    <header className="flex h-14 items-center justify-between border-b border-border/80 bg-white/70 px-6 backdrop-blur">
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="rounded-md border border-border px-3 py-1 text-sm font-medium text-ink transition hover:border-positive hover:text-positive"
          onClick={() => onToday?.()}
        >
          Today
        </button>
        <div className="flex items-center gap-1">
          <button
            type="button"
            className="rounded-md border border-border px-2 py-1 text-sm transition hover:border-positive hover:text-positive"
            onClick={() => onPrev?.()}
          >
            ◀
          </button>
          <button
            type="button"
            className="rounded-md border border-border px-2 py-1 text-sm transition hover:border-positive hover:text-positive"
            onClick={() => onNext?.()}
          >
            ▶
          </button>
        </div>
      </div>
      <div className="text-lg font-semibold text-ink">{periodLabel}</div>
      <div className="flex items-center gap-3">
        <div className="flex rounded-full border border-border bg-white/70 p-1">
          {views.map((view) => (
            <button
              key={view}
              type="button"
              className={classNames(
                'rounded-full px-3 py-1 text-sm capitalize transition',
                viewType === view
                  ? 'bg-positive text-white'
                  : 'text-ink/60 hover:bg-positive/20 hover:text-ink',
              )}
              onClick={() => onViewChange?.(view)}
            >
              {view}
            </button>
          ))}
        </div>
        <button
          type="button"
          className="flex h-8 w-8 items-center justify-center rounded-full border border-border text-sm text-ink transition hover:border-positive hover:text-positive"
          onClick={onToggleInfo}
          aria-label="정보 패널 열기"
        >
          i
        </button>
        <button
          type="button"
          className="rounded-md border border-border px-3 py-1 text-sm text-ink transition hover:border-warning hover:text-warning"
          onClick={onLogout}
        >
          로그아웃
        </button>
      </div>
    </header>
  );
};

export default TopBar;
