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

// Color palette for pie chart segments
const COLORS = [
  'from-indigo-400 to-indigo-500',
  'from-purple-400 to-purple-500',
  'from-pink-400 to-pink-500',
  'from-blue-400 to-blue-500',
  'from-cyan-400 to-cyan-500',
  'from-teal-400 to-teal-500',
  'from-green-400 to-green-500',
  'from-yellow-400 to-yellow-500',
  'from-orange-400 to-orange-500',
  'from-red-400 to-red-500',
];

export function OverviewPieChart({ modelUsage }: OverviewPieChartProps) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  if (!modelUsage || modelUsage.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-indigo-300 text-sm">
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
            boxShadow: '0 4px 12px rgba(79, 70, 229, 0.2)'
          }}
        >
          {/* Center hole for donut effect */}
          <div className="absolute inset-4 bg-white rounded-full flex items-center justify-center">
            <div className="text-center">
              <div className="text-xs text-indigo-400">总计</div>
              <div className="text-lg font-bold text-indigo-600">{totalTokens.toLocaleString()}</div>
            </div>
          </div>
        </div>

        {/* Tooltip */}
        {hoverIndex !== null && modelUsage[hoverIndex] && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="clay-tooltip">
              <div className="font-semibold text-sm">{modelUsage[hoverIndex].model_name}</div>
              <div className="text-indigo-200 text-xs">
                {modelUsage[hoverIndex].total_tokens.toLocaleString()} tokens
              </div>
              <div className="text-indigo-200 text-xs">
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
                ? 'bg-indigo-100 scale-105'
                : 'hover:bg-indigo-50'
            }`}
            onMouseEnter={() => setHoverIndex(index)}
            onMouseLeave={() => setHoverIndex(null)}
          >
            <div
              className={`w-3 h-3 rounded-full bg-gradient-to-br ${COLORS[index % COLORS.length]}`}
            />
            <span className="text-gray-700 max-w-20 truncate" title={item.model_name}>
              {item.model_name}
            </span>
            <span className="text-indigo-500 font-medium ml-1">
              {item.percentage.toFixed(1)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
