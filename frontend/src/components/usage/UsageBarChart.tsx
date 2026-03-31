'use client';

import { useState, useRef, useEffect, useCallback } from 'react';

interface QuarterHourlyTokenData {
  quarter_hour: number;
  tokens: number;
}

interface UsageBarChartProps {
  quarterHourlyDistribution: QuarterHourlyTokenData[];
  days?: number;  // Number of days for trend data (default: 1)
  selectedDate?: string;  // Selected date in YYYY-MM-DD format (user timezone)
}

// Tooltip padding constant for boundary detection
const TOOLTIP_PADDING = 12;

// Format time_slot to label based on days parameter
const formatTimeSlot = (slot: number, totalDays: number, selectedDate?: string): string => {
  const totalMinutes = totalDays * 24 * 60;
  const minutesPerOneSlot = totalMinutes / 96;
  const slotMinutes = slot * minutesPerOneSlot;

  let slotDate: Date;

  if (selectedDate && totalDays === 1) {
    // For single day with selectedDate: use natural day (00:00 to 23:45)
    const [year, month, day] = selectedDate.split('-').map(Number);
    slotDate = new Date(year, month - 1, day, 0, 0, 0, 0);
    slotDate = new Date(slotDate.getTime() + slotMinutes * 60 * 1000);
  } else {
    // For multi-day trends: relative to current time (going backwards)
    const now = new Date();
    const totalEndTime = now.getTime();
    const slotTime = totalEndTime - (totalMinutes * 60 * 1000) + (slotMinutes * 60 * 1000);
    slotDate = new Date(slotTime);
  }

  if (totalDays === 1) {
    // 1 day: show time (e.g., 00:00, 04:00, 08:00, ...)
    const hours = slotDate.getHours();
    const minutes = slotDate.getMinutes();
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
  } else {
    // Multi-day: show month-day (e.g., 3-20, 3-22, 3-24, ...)
    const month = slotDate.getMonth() + 1;
    const day = slotDate.getDate();
    return `${month}-${day}`;
  }
};

// Format time_slot for tooltip (full datetime)
const formatTimeSlotTooltip = (slot: number, totalDays: number, selectedDate?: string): string => {
  const totalMinutes = totalDays * 24 * 60;
  const minutesPerOneSlot = totalMinutes / 96;
  const slotMinutes = slot * minutesPerOneSlot;

  let slotDate: Date;

  if (selectedDate && totalDays === 1) {
    // For single day with selectedDate: use natural day (00:00 to 23:45)
    const [year, month, day] = selectedDate.split('-').map(Number);
    slotDate = new Date(year, month - 1, day, 0, 0, 0, 0);
    slotDate = new Date(slotDate.getTime() + slotMinutes * 60 * 1000);
  } else {
    // For multi-day trends: relative to current time (going backwards)
    const now = new Date();
    const totalEndTime = now.getTime();
    const slotTime = totalEndTime - (totalMinutes * 60 * 1000) + (slotMinutes * 60 * 1000);
    slotDate = new Date(slotTime);
  }

  const month = slotDate.getMonth() + 1;
  const day = slotDate.getDate();
  const hours = slotDate.getHours();
  const minutes = slotDate.getMinutes();

  return `${month}-${day} ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
};

export function UsageBarChart({ quarterHourlyDistribution, days = 1, selectedDate }: UsageBarChartProps) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [mousePosition, setMousePosition] = useState<{ x: number; y: number } | null>(null);
  const [tooltipFlip, setTooltipFlip] = useState<'left' | 'right' | 'top' | 'top-left' | 'top-right' | 'none'>('none');

  const containerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  // Tooltip transform helper - memoized with useCallback
  const getTooltipTransform = useCallback((flip: 'left' | 'right' | 'top' | 'top-left' | 'top-right' | 'none') => {
    switch (flip) {
      case 'left':
        // Near left boundary - show to the right of mouse, above
        return 'translate(0, -100%)';
      case 'right':
        // Near right boundary - show to the left of mouse, above
        return 'translate(-100%, -100%)';
      case 'top':
        // Near top boundary - show below mouse, centered horizontally
        return 'translate(-50%, 0)';
      case 'top-left':
        // Near top and left boundary - show to the right and below
        return 'translate(0, 0)';
      case 'top-right':
        // Near top and right boundary - show to the left and below
        return 'translate(-100%, 0)';
      default:
        // Default - show above mouse, centered horizontally
        return 'translate(-50%, -100%)';
    }
  }, []);

  // Boundary detection for tooltip flip
  useEffect(() => {
    if (!mousePosition || !containerRef.current || !tooltipRef.current) {
      setTooltipFlip('none');
      return;
    }

    const containerRect = containerRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();

    let nearLeft = false;
    let nearRight = false;
    let nearTop = false;

    // Left boundary detection - tooltip would overflow on the left
    if (mousePosition.x < tooltipRect.width / 2 + TOOLTIP_PADDING) {
      nearLeft = true;
    }
    // Right boundary detection - tooltip would overflow on the right
    if (mousePosition.x > containerRect.width - tooltipRect.width / 2 - TOOLTIP_PADDING) {
      nearRight = true;
    }
    // Top boundary detection - tooltip would overflow on the top
    if (mousePosition.y < tooltipRect.height + TOOLTIP_PADDING) {
      nearTop = true;
    }

    let flip: 'left' | 'right' | 'top' | 'top-left' | 'top-right' | 'none' = 'none';
    if (nearTop && nearLeft) {
      flip = 'top-left';
    } else if (nearTop && nearRight) {
      flip = 'top-right';
    } else if (nearLeft) {
      flip = 'left';
    } else if (nearRight) {
      flip = 'right';
    } else if (nearTop) {
      flip = 'top';
    }

    setTooltipFlip(flip);
  }, [mousePosition]);

  if (!quarterHourlyDistribution || quarterHourlyDistribution.length === 0) return null;

  // Sort by quarter_hour and extract token values
  const sortedData = [...quarterHourlyDistribution].sort((a, b) => a.quarter_hour - b.quarter_hour);
  const chartData = sortedData.map(d => d.tokens);
  const maxValue = Math.max(...chartData, 1);

  // Calculate label indices based on days parameter
  let labelIndices: number[];
  if (days === 1) {
    // 1 day: show labels at every 4 hours (0:00, 4:00, 8:00, 12:00, 16:00, 20:00)
    labelIndices = [0, 16, 32, 48, 64, 80];
  } else if (days === 7) {
    // 7 days: show labels every ~1.5 days (6 slots each)
    labelIndices = [0, 14, 29, 43, 58, 73, 87, 95];
  } else if (days === 30) {
    // 30 days: show labels every ~5 days (16 slots each)
    labelIndices = [0, 16, 32, 48, 64, 80, 95];
  } else {
    // Default: show 6 evenly spaced labels
    const step = Math.floor(96 / 5);
    labelIndices = Array.from({ length: 6 }, (_, i) => Math.min(i * step, 95));
  }

  // Prevent division by zero
  const safeLength = Math.max(chartData.length - 1, 1);

  return (
    <div className="flex flex-col h-full py-1">
      {/* Chart bars */}
      <div ref={containerRef} className="flex items-end flex-1 border-b-2 border-indigo-200/50 relative px-3 justify-between gap-px">
        {chartData.map((value, idx) => (
          <div
            key={idx}
            className="clay-chart-bar w-2 bg-gradient-to-t from-indigo-400 to-purple-400 hover:from-indigo-500 hover:to-purple-500 transition-all duration-200 cursor-pointer shrink-0"
            style={{
              height: value > 0 ? `${Math.max((value / maxValue) * 100, 3)}%` : '0%'
            }}
            onMouseMove={(e) => {
              if (!containerRef.current) return;
              const rect = containerRef.current.getBoundingClientRect();
              setMousePosition({
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
              });
            }}
            onMouseEnter={() => setHoverIndex(idx)}
            onMouseLeave={() => {
              setHoverIndex(null);
              setMousePosition(null);
            }}
            role="graphics-symbol"
            aria-label={`${formatTimeSlot(sortedData[idx].quarter_hour, days, selectedDate)} - ${chartData[idx]} tokens`}
          />
        ))}
        {/* Tooltip overlay */}
        {hoverIndex !== null && mousePosition && (
          <div
            ref={tooltipRef}
            className="absolute pointer-events-none z-30 tooltip-transition"
            style={{
              left: mousePosition.x,
              top: mousePosition.y,
              transform: getTooltipTransform(tooltipFlip)
            }}
          >
            <div className="clay-tooltip">
              <span className="font-semibold text-sm">{chartData[hoverIndex]} tokens</span>
              <br />
              <span className="text-indigo-200 text-xs">
                {formatTimeSlotTooltip(sortedData[hoverIndex].quarter_hour, days, selectedDate)}
              </span>
            </div>
          </div>
        )}
      </div>
      {/* Hour axis */}
      <div className="flex justify-between text-[10px] text-indigo-400 font-medium mt-1 px-3 relative">
        {labelIndices.map((idx) => {
          const isFirst = idx === 0;

          const leftPercent = isFirst ? 0 : (idx / safeLength) * 100;

          return (
            <span
              key={idx}
              className={`absolute transform ${isFirst ? '' : '-translate-x-1/2'}`}
              style={{ left: `${leftPercent}%` }}
            >
              {formatTimeSlot(idx, days, selectedDate)}
            </span>
          );
        })}
      </div>
    </div>
  );
}
