import { useEffect, useRef } from 'react';

/**
 * Custom hook that runs an interval callback only when the page is visible.
 * Automatically pauses when the user switches to another tab and resumes when they return.
 *
 * @param callback - Function to call on each interval
 * @param delay - Interval delay in milliseconds, or null to disable the interval
 */
export function useIntervalOnVisible(callback: () => void, delay: number | null) {
  const savedCallback = useRef(callback);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isRunningRef = useRef(false);

  // Keep the callback ref updated
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    console.log('[useIntervalOnVisible] Effect running, delay:', delay, 'visibility:', document.visibilityState);

    if (delay === null) {
      console.log('[useIntervalOnVisible] Delay is null, stopping any existing interval');
      // Stop interval if delay is null
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
        isRunningRef.current = false;
      }
      return;
    }

    const startInterval = () => {
      if (isRunningRef.current) {
        console.log('[useIntervalOnVisible] Interval already running, skipping start');
        return; // Prevent multiple intervals
      }
      console.log('[useIntervalOnVisible] Starting interval with delay:', delay);
      isRunningRef.current = true;
      intervalRef.current = setInterval(() => {
        console.log('[useIntervalOnVisible] Interval triggered');
        savedCallback.current();
      }, delay);
    };

    const stopInterval = () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      isRunningRef.current = false;
    };

    const handleVisibilityChange = () => {
      console.log('[useIntervalOnVisible] Visibility changed to:', document.visibilityState);
      if (document.visibilityState === 'visible') {
        startInterval();
        // Immediately execute the callback when the page becomes visible
        console.log('[useIntervalOnVisible] Page visible, executing callback immediately');
        savedCallback.current();
      } else {
        stopInterval();
      }
    };

    // Check initial state - if page is visible, start interval
    if (document.visibilityState === 'visible') {
      startInterval();
    }

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      console.log('[useIntervalOnVisible] Cleanup - stopping interval and removing listener');
      stopInterval();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [delay]);
}
