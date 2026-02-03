'use client';

import { useState, useRef, useEffect, useCallback } from 'react';

interface HourlyTokenData {
  hour: number;
  tokens: number;
}

interface UsageBarChartProps {
  hourlyDistribution: HourlyTokenData[];
}

// Tooltip padding constant for boundary detection
const TOOLTIP_PADDING = 12;

export function UsageBarChart({ hourlyDistribution }: UsageBarChartProps) {
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

  if (!hourlyDistribution || hourlyDistribution.length === 0) return null;

  // Sort by hour and extract token values
  const sortedData = [...hourlyDistribution].sort((a, b) => a.hour - b.hour);
  const chartData = sortedData.map(d => d.tokens);
  const maxValue = Math.max(...chartData, 1);

  // Calculate label indices (show labels at 0, 6, 12, 18)
  const labelIndices = sortedData
    .map((d, idx) => ({ idx, hour: d.hour }))
    .filter(({ hour }) => hour === 0 || hour === 6 || hour === 12 || hour === 18)
    .map(({ idx }) => idx);

  // Prevent division by zero
  const safeLength = Math.max(chartData.length - 1, 1);

  return (
    <div className="flex flex-col h-full py-0.5">
      {/* Chart bars */}
      <div ref={containerRef} className="flex items-end flex-1 border-b border-gray-200 relative px-3 justify-between">
        {chartData.map((value, idx) => (
          <div
            key={idx}
            className="w-3 bg-green-400 hover:bg-green-500 transition-colors cursor-pointer shrink-0"
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
            aria-label={`${sortedData[idx].hour}:00 - ${chartData[idx]} tokens`}
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
            <div className="bg-gray-900 text-white text-[10px] rounded py-0.5 px-2 whitespace-nowrap shadow-md">
              <span className="font-semibold">{chartData[hoverIndex]} tokens</span>
              <br />
              <span className="text-gray-300 text-[9px]">
                {sortedData[hoverIndex].hour}:00
              </span>
            </div>
          </div>
        )}
      </div>
      {/* Hour axis */}
      <div className="flex justify-between text-[10px] text-gray-400 mt-0.5 px-3 relative">
        {labelIndices.map((idx) => {
          const leftPercent = (idx / safeLength) * 100;
          return (
            <span
              key={idx}
              className="absolute transform -translate-x-1/2"
              style={{ left: `${leftPercent}%` }}
            >
              {sortedData[idx].hour}:00
            </span>
          );
        })}
      </div>
    </div>
  );
}
