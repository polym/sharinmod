'use client';

import { useEffect, useState, useMemo, useRef, useCallback } from 'react';
import { MoreVertical } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { ShareAPIKeyDialog } from '@/components/share-token-dialog';
import { apiKeyAPI } from '@/lib/services';
import { SharedAPIKey, SharedAPIKeyMetrics, ChartDataPoint } from '@/types/apiKey';
import { useIntervalOnVisible } from '@/hooks/useIntervalOnVisible';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

// Modern square toggle switch component with custom soft colors
function SquareSwitch({ 
  checked, 
  onCheckedChange,
  disabled = false
}: { 
  checked: boolean; 
  onCheckedChange: (checked: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={() => !disabled && onCheckedChange(!checked)}
      disabled={disabled}
      role="switch"
      aria-checked={checked}
      aria-label={checked ? "启用" : "禁用"}
      className={`
        relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center 
        rounded-md transition-all duration-200 ease-in-out
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2
        disabled:cursor-not-allowed disabled:opacity-50
        ${checked ? 'bg-switch-on border border-green-300' : 'bg-switch-off'}
      `}
    >
      <span
        className={`
          pointer-events-none inline-block h-4 w-4 transform rounded bg-white shadow-lg
          transition-transform duration-200 ease-in-out mx-1
          ${checked ? 'translate-x-4' : 'translate-x-0'}
        `}
      />
    </button>
  );
}

// Token formatting helper - formats raw token value for display
function formatTokens(totalTokens: number): { value: number; unit: string } {
  if (totalTokens >= 1_000_000) {
    return { value: Math.round(totalTokens / 1_000_000 * 10) / 10, unit: '百万' };
  } else {
    return { value: Math.round(totalTokens / 10_000 * 10) / 10, unit: '万' };
  }
}

// Tooltip padding constant for boundary detection
const TOOLTIP_PADDING = 12;

// 48-hour bar chart component with hour axis
function UsageBarChart({ data }: { data: ChartDataPoint[] }) {
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

  // Pre-compute chart data
  const chartData = data ? data.map(d => d.value) : [];
  const maxValue = chartData.length > 0 ? Math.max(...chartData, 1) : 1;

  // Parse UTC date string and return components with UTC+8 offset
  const parseBeijingTime = (dateStr: string) => {
    // Backend returns format: "YYYY-MM-DD HH:00" (UTC)
    const [ymd, time] = dateStr.split(' ');
    const [year, month, day] = ymd.split('-').map(Number);
    const [hour, minute] = time.split(':').map(Number);
    // Add 8 hours for Beijing time
    const beijingHour = (hour + 8) % 24;
    // Handle date rollover when crossing midnight
    const date = new Date(Date.UTC(year, month - 1, day, beijingHour, minute));
    return {
      month: date.getUTCMonth() + 1,
      day: date.getUTCDate(),
      hour: date.getUTCHours()
    };
  };

  // Memoize label indices calculation (based on UTC+8 hour)
  const labelIndices = useMemo(() => {
    const indices: number[] = [];
    if (!data) return indices;
    data.forEach((_, idx) => {
      const { hour } = parseBeijingTime(data[idx].date);
      if (hour === 0 || hour === 12) {
        indices.push(idx);
      }
    });
    return indices;
  }, [data]);

  // Memoize label content (formatted in UTC+8)
  const labelContent = useMemo(() => {
    const content: { [key: number]: string } = {};
    if (!data) return content;
    data.forEach((d, idx) => {
      const { month, day, hour } = parseBeijingTime(d.date);
      if (hour === 0 || hour === 12) {
        content[idx] = `${month}/${day} ${hour.toString().padStart(2, '0')}:00`;
      }
    });
    return content;
  }, [data]);

  // Early return after all hooks
  if (!data || data.length === 0) return null;

  // Prevent division by zero
  const safeLength = Math.max(chartData.length - 1, 1);

  return (
    <div className="flex flex-col h-full py-0.5">
      {/* Chart bars */}
      <div ref={containerRef} className="flex items-end flex-1 border-b border-gray-200 relative px-3 justify-between gap-px">
        {chartData.map((value, idx) => {
          const timeInfo = parseBeijingTime(data[idx].date);
          return (
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
              aria-label={`${timeInfo.month}/${timeInfo.day} ${timeInfo.hour.toString().padStart(2, '0')}:00 - ${chartData[idx]} tokens`}
            />
          );
        })}
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
                {parseBeijingTime(data[hoverIndex].date).month}/{parseBeijingTime(data[hoverIndex].date).day} {parseBeijingTime(data[hoverIndex].date).hour.toString().padStart(2, '0')}:00
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
              {labelContent[idx]}
            </span>
          );
        })}
      </div>
    </div>
  );
}

export function MySharedPage() {
  const [sharedAPIKeys, setSharedAPIKeys] = useState<SharedAPIKey[]>([]);
  const [metricsMap, setMetricsMap] = useState<{[key: number]: SharedAPIKeyMetrics}>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSharedAPIKeys();
  }, []);

  const loadSharedAPIKeys = async () => {
    try {
      const response = await apiKeyAPI.getMySharedAPIKeys();
      const keys = response.data.items;
      setSharedAPIKeys(keys);
      
      // Load metrics for each key
      for (const key of keys) {
        loadMetrics(key.id);
      }
    } catch (error) {
      console.error('Failed to load shared API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMetrics = async (apiKeyId: number) => {
    try {
      const response = await apiKeyAPI.getSharedAPIKeyMetrics(apiKeyId);
      setMetricsMap(prev => ({
        ...prev,
        [apiKeyId]: response.data
      }));
    } catch (error) {
      console.error(`Failed to load metrics for API key ${apiKeyId}:`, error);
    }
  };

  // Auto-refresh all metrics every minute when page is visible
  const refreshAllMetrics = async () => {
    if (sharedAPIKeys.length === 0) return;
    try {
      for (const key of sharedAPIKeys) {
        await loadMetrics(key.id);
      }
    } catch (error) {
      // Silently fail
    }
  };

  useIntervalOnVisible(refreshAllMetrics, sharedAPIKeys.length > 0 ? 20000 : null);

  const handleDisableAPIKey = async (apiKeyId: number) => {
    try {
      await apiKeyAPI.disableSharedAPIKey(apiKeyId);
      await loadSharedAPIKeys();
    } catch (error) {
      console.error('Failed to disable API key:', error);
      alert('停用失败，请重试');
    }
  };

  const handleEnableAPIKey = async (apiKeyId: number) => {
    try {
      await apiKeyAPI.enableSharedAPIKey(apiKeyId);
      await loadSharedAPIKeys();
    } catch (error) {
      console.error('Failed to enable API key:', error);
      alert('启用失败，请重试');
    }
  };

  const handleDeleteAPIKey = async (apiKeyId: number) => {
    if (!confirm('确定要删除这个订阅吗？此操作不可撤销。')) {
      return;
    }
    try {
      await apiKeyAPI.deleteSharedAPIKey(apiKeyId);
      await loadSharedAPIKeys();
    } catch (error) {
      console.error('Failed to delete API key:', error);
      alert('删除失败，请重试');
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-8">
      <Card>
        <CardHeader className="p-6">
          <div className="flex justify-between items-center">
            <div className="flex flex-col space-y-1.5">
              <h3 className="text-xl font-semibold leading-none tracking-tight">管理订阅</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">添加、启用、停用或删除您的订阅 Keys</p>
            </div>
            <ShareAPIKeyDialog onAPIKeyShared={loadSharedAPIKeys}>
              <Button variant="ghost" className="bg-brand-100 hover:bg-brand-400 text-brand-500 border border-brand-500">
                绑定新订阅
              </Button>
            </ShareAPIKeyDialog>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-gray-500">加载中...</div>
            </div>
          ) : sharedAPIKeys.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-500 mb-4">暂无绑定的订阅</div>
              <ShareAPIKeyDialog onAPIKeyShared={loadSharedAPIKeys}>
                <Button variant="outline">
                  绑定您的第一个订阅
                </Button>
              </ShareAPIKeyDialog>
            </div>
          ) : (
            <div className="space-y-4">
              {sharedAPIKeys.map((apiKey) => (
                <div
                  key={apiKey.id}
                  className={`p-5 border rounded-lg space-y-4 ${
                    apiKey.status !== 'active' ? 'opacity-50 grayscale' : ''
                  }`}
                >
                  {/* Top Section: Logo, Provider Info, and Buttons */}
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                    <div className="flex items-center gap-4">
                      {/* Provider Logo */}
                      {apiKey.provider_logo_path ? (
                        <img 
                          src={apiKey.provider_logo_path} 
                          alt={apiKey.provider_display_name || apiKey.provider}
                          className="w-14 h-14 rounded-full object-cover border border-gray-200"
                          onError={(e) => {
                            // Fallback to first letter if image fails to load
                            (e.target as HTMLImageElement).style.display = 'none';
                          }}
                        />
                      ) : (
                        <div className="w-14 h-14 rounded-full bg-brand-100 flex items-center justify-center text-brand-600 font-bold text-xl">
                          {(apiKey.provider_display_name || apiKey.provider || 'A').charAt(0).toUpperCase()}
                        </div>
                      )}
                      
                      {/* Provider Name - Title is clickable */}
                      <div>
                        {apiKey.provider_website ? (
                          <a
                            href={apiKey.provider_website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-semibold text-lg text-gray-900 hover:text-brand-600 transition-colors cursor-pointer"
                          >
                            {apiKey.provider_display_name || apiKey.provider}
                          </a>
                        ) : (
                          <div className="font-semibold text-lg text-gray-900">
                            {apiKey.provider_display_name || apiKey.provider}
                          </div>
                        )}
                        {/* Model Tags */}
                        {apiKey.supported_models && apiKey.supported_models.length > 0 && (
                          <div className="flex gap-2 flex-wrap mt-1">
                            {apiKey.supported_models.map((model) => (
                              <span
                                key={model}
                                className="px-2.5 py-0.5 bg-white text-gray-700 text-xs rounded border border-gray-200"
                              >
                                {model}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Square Toggle Switch and Delete Menu */}
                    <div className="flex items-center gap-3">
                      <SquareSwitch
                        checked={apiKey.status === 'active'}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            handleEnableAPIKey(apiKey.id);
                          } else {
                            handleDisableAPIKey(apiKey.id);
                          }
                        }}
                      />

                      {/* Dropdown Menu for Delete */}
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            className="text-red-600 cursor-pointer focus:text-red-600"
                            onClick={() => handleDeleteAPIKey(apiKey.id)}
                          >
                            删除
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>

                  {/* Stats and Chart Section - ~25%:75% ratio (excluding gap) */}
                  {metricsMap[apiKey.id] && (
                    <div className="flex flex-col sm:flex-row gap-4 pt-2">
                      {/* Statistics - 1 part */}
                      <dl className="sm:flex-[1] flex flex-row gap-4 sm:gap-6 items-center">
                        <div className="flex flex-col">
                          <dt className="text-xs text-gray-500">总Token</dt>
                          <dd className="text-2xl font-semibold text-gray-900">
                            {(() => {
                              const { value, unit } = formatTokens(metricsMap[apiKey.id].total_tokens);
                              return <>{value}<span className="text-sm font-normal text-gray-500 ml-1">{unit}</span></>;
                            })()}
                          </dd>
                        </div>
                        <div className="flex flex-col">
                          <dt className="text-xs text-gray-500">总时长</dt>
                          <dd className="text-2xl font-semibold text-gray-900">
                            {metricsMap[apiKey.id].total_duration_days}<span className="text-sm font-normal text-gray-500 ml-1">天</span>
                          </dd>
                        </div>
                        <div className="flex flex-col">
                          <dt className="text-xs text-gray-500">总请求</dt>
                          <dd className="text-2xl font-semibold text-gray-900">
                            {metricsMap[apiKey.id].total_requests}<span className="text-sm font-normal text-gray-500 ml-1">次</span>
                          </dd>
                        </div>
                      </dl>
                      
                      {/* 48-hour Bar Chart - 75% width (sm:flex-[3] of 4 total) */}
                      <div className="sm:flex-[3] border border-gray-200 rounded overflow-hidden h-40">
                        <div className="p-2 pt-2 pb-5 h-full">
                          <UsageBarChart data={metricsMap[apiKey.id].chart_data} />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
