import { NavLink } from 'react-router-dom';
import classNames from 'classnames';

interface SidebarProps {
  currentPath: string;
  onToggleInfo: () => void;
}

const menuItems = [
  { to: '/home/weekly', label: '주간' },
  { to: '/home/monthly', label: '월간' },
];

const Sidebar = ({ currentPath, onToggleInfo }: SidebarProps) => {
  return (
    <aside className="flex w-16 flex-col items-center bg-white/70 py-6 shadow-sm backdrop-blur">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-border">
        <div className="grid grid-cols-3 gap-0.5">
          {Array.from({ length: 9 }).map((_, index) => (
            <span key={index} className="h-1.5 w-1.5 rounded-full bg-positive" />
          ))}
        </div>
      </div>
      <nav className="mt-8 flex flex-1 flex-col items-center gap-4">
        {menuItems.map((item) => {
          const isActive = currentPath.startsWith(item.to);
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={classNames(
                'flex h-10 w-10 items-center justify-center rounded-full text-xs font-medium transition',
                isActive
                  ? 'bg-positive/80 text-white'
                  : 'text-ink/60 hover:bg-positive/20 hover:text-ink',
              )}
            >
              {item.label.substring(0, 2)}
            </NavLink>
          );
        })}
      </nav>
      <div className="mt-auto flex flex-col items-center gap-3">
        <button
          type="button"
          className="flex h-10 w-10 items-center justify-center rounded-full border border-border text-[11px] text-ink/60 transition hover:border-positive hover:text-positive"
          onClick={onToggleInfo}
        >
          Info
        </button>
        <span className="text-[10px] text-ink/40">v1.0</span>
      </div>
    </aside>
  );
};

export default Sidebar;
