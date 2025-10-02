import { useEffect, useCallback } from 'react';
import autoRefreshService from '@/lib/auto-refresh';

export const useAutoRefresh = (
  type: 'flags' | 'chart',
  callback: () => void | Promise<void>
) => {
  const handleAutoRefresh = useCallback(async () => {
    await callback();
  }, [callback]);

  useEffect(() => {
    // Register for auto-refresh updates
    autoRefreshService[`on${type.charAt(0).toUpperCase() + type.slice(1)}Update` as 'onFlagsUpdate' | 'onChartUpdate'](handleAutoRefresh);
    
    // Start auto-refresh service if not already running
    if (!autoRefreshService.getStatus().isRunning) {
      autoRefreshService.start();
    }

    return () => {
      // Unregister callback when component is destroyed
      autoRefreshService.off(type, handleAutoRefresh);
    };
  }, [type, handleAutoRefresh]);

  return {
    status: autoRefreshService.getStatus(),
    enable: autoRefreshService.enable,
    disable: autoRefreshService.disable,
    setInterval: autoRefreshService.setInterval,
  };
};
