'use client';

import { useState } from 'react';

interface ModelUsageData {
  model_name: string;
  total_tokens: number;
  percentage: number;
}

interface OverviewPieChartProps {
  modelUsage: ModelUsageData[];
}

// Color palette for pie chart segments (hex colors for conic-gradient and legend)
const COLORS = [
  '#1ed760',
  '#b3b3b3',
  '#4d4d4d',
  '#1fdf64',
  '#535353',
  '#7c7c7c',
  '#1abc9c',
  '#3498db',
  '#9b59b6',
  '#e67e22',
];

export function OverviewPieChart({ modelUsage }: OverviewPieChartProps) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  if (!modelUsage || modelUsage.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-[#535353] text-sm">
        暂无数据
      </div>
    );
  }

  // Calculate cumulative percentages for conic-gradient
  let cumulativePercent = 0;
  const gradientStops = modelUsage.map((item, index) => {
    const startPercent = cumulativePercent;
    cumulativePercent += item.percentage;
    const endPercent = cumulativePercent;
    return { startPercent, endPercent, color: COLORS[index % COLORS.length], index };
  });

  // Generate conic-gradient string
  const gradientString = gradientStops
    .map(stop => `${stop.color} ${stop.startPercent.toFixed(1)}% ${stop.endPercent.toFixed(1)}%`)
    .join(', ');

  const totalTokens = modelUsage.reduce((sum, item) => sum + item.total_tokens, 0);

  return (
    <div className="flex flex-col h-full">
      {/* Pie chart */}
      <div className="flex-1 flex items-center justify-center relative">
        <div
          className="w-40 h-40 rounded-full relative"
          style={{
            background: `conic-gradient(${gradientString})`,
            boxShadow: '0 4px 16px rgba(0,0,0,0.5)'
          }}
        >
          {/* Center hole for donut effect */}
          <div className="absolute inset-4 bg-[#181818] rounded-full flex items-center justify-center">
            <div className="text-center">
              <div className="text-xs text-[#535353]">总计</div>
              <div className="text-lg font-bold text-[#b3b3b3]">{totalTokens.toLocaleString()}</div>
            </div>
          </div>
        </div>

        {/* Tooltip */}
        {hoverIndex !== null && modelUsage[hoverIndex] && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="bg-[#282828] text-white rounded-lg px-3 py-2 shadow-[0_4px_16px_rgba(0,0,0,0.5)] text-sm">
              <div className="font-semibold text-sm">{modelUsage[hoverIndex].model_name}</div>
              <div className="text-[#535353] text-xs">
                {modelUsage[hoverIndex].total_tokens.toLocaleString()} tokens
              </div>
              <div className="text-[#535353] text-xs">
                {modelUsage[hoverIndex].percentage.toFixed(1)}%
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-2 justify-center mt-3">
        {modelUsage.map((item, index) => (
          <div
            key={index}
            className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs cursor-pointer transition-all ${
              hoverIndex === index
                ? 'bg-[#282828] scale-105'
                : 'hover:bg-[#1f1f1f]'
            }`}
            onMouseEnter={() => setHoverIndex(index)}
            onMouseLeave={() => setHoverIndex(null)}
          >
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: COLORS[index % COLORS.length] }}
            />
            <span className="text-[#b3b3b3] max-w-20 truncate" title={item.model_name}>
              {item.model_name}
            </span>
            <span className="text-[#b3b3b3] font-medium ml-1">
              {item.percentage.toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
