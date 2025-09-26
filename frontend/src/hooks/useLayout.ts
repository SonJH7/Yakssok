import { useCallback, useContext } from 'react';
import { LayoutConfigContext, HeaderConfig } from '../components/Layout/Layout';

export const useLayout = () => {
  const context = useContext(LayoutConfigContext);
  if (!context) {
    throw new Error('Layout 컨텍스트를 찾을 수 없습니다.');
  }

  const setHeader = useCallback(
    (config: HeaderConfig) => {
      context.setHeaderConfig({
        periodLabel: config.periodLabel,
        onPrev: config.onPrev,
        onNext: config.onNext,
        onToday: config.onToday,
        viewType: config.viewType,
        onViewChange: config.onViewChange,
      });
    },
    [context],
  );

  const updateHeader = useCallback(
    (config: Partial<HeaderConfig>) => {
      context.setHeaderConfig(config);
    },
    [context],
  );

  return { setHeader, updateHeader };
};
