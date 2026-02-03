'use client';

import { useState } from 'react';

interface HourlyTokenData {
  hour: number;
  tokens: number;
}

interface UsageBarChartProps {
  hourlyDistribution: HourlyTokenData[];
}

export function UsageBarChart({ hourlyDistribution }: UsageBarChartProps) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

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
      <div className="flex items-end flex-1 border-b border-gray-200 relative">
        {chartData.map((value, idx) => (
          <div
            key={idx}
            className="flex-1 bg-green-400 hover:bg-green-500 transition-colors cursor-pointer"
            style={{
              height: `${Math.max((value / maxValue) * 100, 3)}%`,
              marginLeft: idx === 0 ? 0 : '1px'
            }}
            onMouseEnter={() => setHoverIndex(idx)}
            onMouseLeave={() => setHoverIndex(null)}
          />
        ))}
        {/* Tooltip overlay */}
        {hoverIndex !== null && (
          <div
            className="absolute pointer-events-none z-30 flex flex-col items-center gap-0.5"
            style={{
              bottom: `${Math.max((chartData[hoverIndex] / maxValue) * 100, 3)}%`,
              left: `${(hoverIndex / safeLength) * 100}%`,
              transform: 'translate(-50%, -100%)',
              marginBottom: '-2px'
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
      <div className="flex justify-between text-[10px] text-gray-400 mt-0.5 px-0.5 relative">
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
