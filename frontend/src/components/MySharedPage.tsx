'use client';

import { useEffect, useState, useMemo, useRef, useCallback } from 'react';
import { MoreVertical } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { ShareAPIKeyDialog } from '@/components/share-token-dialog';
import { EditSubscriptionDialog } from '@/components/edit-subscription-dialog';
import { apiKeyAPI } from '@/lib/services';
import { SharedAPIKey, SharedAPIKeyMetrics, ChartDataPoint } from '@/types/apiKey';
import { useIntervalOnVisible } from '@/hooks/useIntervalOnVisible';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Switch } from '@/components/ui/switch';
import { useTranslations } from 'next-intl';
import { useAuthStore } from '@/lib/store';

// Token formatting helper - formats raw token value for display
function formatTokens(totalTokens: number, unitMillion: string, unitTenThousand: string): { value: number; unit: string } {
  if (totalTokens >= 1_000_000) {
    return { value: Math.round(totalTokens / 1_000_000 * 10) / 10, unit: unitMillion };
  } else {
    return { value: Math.round(totalTokens / 10_000 * 10) / 10, unit: unitTenThousand };
  }
}

// Tooltip padding constant for boundary detection
const TOOLTIP_PADDING = 12;

// Helper function to remove organization suffix from model name
function getModelDisplayName(modelName: string): string {
  return modelName.replace(/@org-\d+$/, '');
}

// 48-hour bar chart component with hour axis
function UsageBarChart({ data }: { data: ChartDataPoint[] }) {
  const tCommon = useTranslations('common');
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [mousePosition, setMousePosition] = useState<{ x: number; y: number } | null>(null);
  const [tooltipFlip, setTooltipFlip] = useState<'left' | 'right' | 'top' | 'top-left' | 'top-right' | 'none'>('none');

  const containerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  // Tooltip transform helper - memoized with useCallback
  const getTooltipTransform = useCallback((flip: 'left' | 'right' | 'top' | 'top-left' | 'top-right' | 'none') => {
    switch (flip) {
      case 'left':
        return 'translate(0, -100%)';
      case 'right':
        return 'translate(-100%, -100%)';
      case 'top':
        return 'translate(-50%, 0)';
      case 'top-left':
        return 'translate(0, 0)';
      case 'top-right':
        return 'translate(-100%, 0)';
      default:
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

    if (mousePosition.x < tooltipRect.width / 2 + TOOLTIP_PADDING) {
      nearLeft = true;
    }
    if (mousePosition.x > containerRect.width - tooltipRect.width / 2 - TOOLTIP_PADDING) {
      nearRight = true;
    }
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

  // Parse RFC3339 UTC date string and return components in local timezone
  const parseLocalTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return {
      month: date.getMonth() + 1,
      day: date.getDate(),
      hour: date.getHours()
    };
  };

  // Memoize label indices calculation (based on local timezone hour)
  const labelIndices = useMemo(() => {
    const indices: number[] = [];
    if (!data) return indices;
    data.forEach((_, idx) => {
      const { hour } = parseLocalTime(data[idx].date);
      if (hour === 0 || hour === 12) {
        indices.push(idx);
      }
    });
    return indices;
  }, [data]);

  // Memoize label content (formatted in local timezone)
  const labelContent = useMemo(() => {
    const content: { [key: number]: string } = {};
    if (!data) return content;
    data.forEach((d, idx) => {
      const { month, day, hour } = parseLocalTime(d.date);
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
    <div className="flex flex-col h-full py-1">
      {/* Chart bars */}
      <div ref={containerRef} className="flex items-end flex-1 border-b-2 border-[#4d4d4d] relative px-3 justify-between gap-px">
        {chartData.map((value, idx) => {
          const timeInfo = parseLocalTime(data[idx].date);
          return (
            <div
              key={idx}
              className="w-3 bg-[#1ed760] hover:bg-[#1ed760]/80 transition-all duration-200 cursor-pointer shrink-0 rounded-t-sm"
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
            <div className="bg-[#282828] text-white text-xs rounded-lg py-1.5 px-3 whitespace-nowrap shadow-[0_4px_16px_rgba(0,0,0,0.5)]">
              <span className="font-bold">{chartData[hoverIndex]} {tCommon('tokens')}</span>
              <br />
              <span className="text-[#535353] text-[10px]">
                {parseLocalTime(data[hoverIndex].date).month}/{parseLocalTime(data[hoverIndex].date).day} {parseLocalTime(data[hoverIndex].date).hour.toString().padStart(2, '0')}:00
              </span>
            </div>
          </div>
        )}
      </div>
      {/* Hour axis */}
      <div className="flex justify-between text-[10px] text-[#535353] mt-1 px-3 relative">
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
  const t = useTranslations('shared');
  const tCommon = useTranslations('common');
  const tStats = useTranslations('shared.stats');
  const { currentOrganization } = useAuthStore();

  const [sharedAPIKeys, setSharedAPIKeys] = useState<SharedAPIKey[]>([]);
  const [metricsMap, setMetricsMap] = useState<{[key: number]: SharedAPIKeyMetrics}>({});
  const [loading, setLoading] = useState(true);
  const [editingApiKey, setEditingApiKey] = useState<SharedAPIKey | null>(null);

  useEffect(() => {
    loadSharedAPIKeys();
  }, [currentOrganization]);

  const loadSharedAPIKeys = async () => {
    try {
      const response = await apiKeyAPI.getMySharedAPIKeys(currentOrganization?.id);
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
      await apiKeyAPI.disableSharedAPIKey(apiKeyId, currentOrganization?.id);
      await loadSharedAPIKeys();
    } catch (error) {
      console.error('Failed to disable API key:', error);
      alert(t('disableFailed'));
    }
  };

  const handleEnableAPIKey = async (apiKeyId: number) => {
    try {
      await apiKeyAPI.enableSharedAPIKey(apiKeyId, currentOrganization?.id);
      await loadSharedAPIKeys();
    } catch (error) {
      console.error('Failed to enable API key:', error);
      alert(t('enableFailed'));
    }
  };

  const handleDeleteAPIKey = async (apiKeyId: number) => {
    if (!confirm(t('confirmDelete'))) {
      return;
    }
    try {
      await apiKeyAPI.deleteSharedAPIKey(apiKeyId, currentOrganization?.id);
      await loadSharedAPIKeys();
    } catch (error) {
      console.error('Failed to delete API key:', error);
      alert(t('deleteFailed'));
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-8">
      <Card className=" border border-[#282828] bg-[#181818]">
        <CardHeader className="p-6">
          <div className="flex justify-between items-center">
            <div className="flex flex-col space-y-2">
              <h3 className="text-2xl font-bold leading-none tracking-tight text-white">{t('title')}</h3>
              <p className="text-sm text-[#b3b3b3] font-medium">{t('description')}</p>
            </div>
            <ShareAPIKeyDialog onAPIKeyShared={loadSharedAPIKeys}>
              <Button className="">
                {t('bindNew')}
              </Button>
            </ShareAPIKeyDialog>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-[#b3b3b3] font-medium">{t('loading')}</div>
            </div>
          ) : sharedAPIKeys.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-[#b3b3b3] font-medium mb-6">{t('noBindings')}</div>
              <ShareAPIKeyDialog onAPIKeyShared={loadSharedAPIKeys}>
                <Button className="">
                  {t('bindFirst')}
                </Button>
              </ShareAPIKeyDialog>
            </div>
          ) : (
            <div className="space-y-5">
              {sharedAPIKeys.map((apiKey) => (
                <div
                  key={apiKey.id}
                  className={` p-6 border border-[#282828] bg-[#181818] space-y-4 rounded-2xl ${
                    apiKey.status !== 'active' ? 'opacity-50 grayscale-[0.5]' : ''
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
                          className="w-16 h-16 rounded-2xl object-cover border-2 border-[#4d4d4d] bg-[#181818] p-1 shadow-md"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none';
                          }}
                        />
                      ) : (
                        <div className="w-16 h-16 rounded-2xl bg-[#282828] flex items-center justify-center text-[#b3b3b3] font-bold text-2xl border border-[#4d4d4d]">
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
                            className="font-bold text-xl text-white hover:text-[#b3b3b3] transition-colors cursor-pointer"
                          >
                            {apiKey.provider_display_name || apiKey.provider}
                          </a>
                        ) : (
                          <div className="font-bold text-xl text-white">
                            {apiKey.provider_display_name || apiKey.provider}
                          </div>
                        )}
                        {/* Model Tags */}
                        {apiKey.supported_models && apiKey.supported_models.length > 0 && (
                          <div className="flex gap-2 flex-wrap mt-2">
                            {apiKey.supported_models.map((model) => (
                              <span
                                key={model}
                                className="  px-3 py-1 text-xs font-medium"
                              >
                                {getModelDisplayName(model)}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Toggle Switch and Delete Menu */}
                    <div className="flex items-center gap-3">
                      <Switch
                        checked={apiKey.status === 'active'}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            handleEnableAPIKey(apiKey.id);
                          } else {
                            handleDisableAPIKey(apiKey.id);
                          }
                        }}
                        aria-label={apiKey.status === 'active' ? t('statusEnabled') : t('statusDisabled')}
                      />

                      {/* Dropdown Menu for Delete */}
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm" className="h-10 w-10 p-0 rounded-xl hover:bg-[#282828]">
                            <MoreVertical className="h-5 w-5 text-[#b3b3b3]" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            className="cursor-pointer"
                            onClick={() => setEditingApiKey(apiKey)}
                          >
                            {t('edit')}
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-red-600 cursor-pointer focus:text-red-600"
                            onClick={() => handleDeleteAPIKey(apiKey.id)}
                          >
                            {t('delete')}
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
                  </div>

                  {/* Stats and Chart Section */}
                  {metricsMap[apiKey.id] && (
                    <div className="flex flex-col sm:flex-row gap-5 pt-3">
                      {/* Statistics */}
                      <dl className="sm:flex-[1] flex flex-row gap-5 sm:gap-7 items-center">
                        <div className="flex flex-col">
                          <dt className="text-xs font-semibold text-[#b3b3b3] mb-1">{tStats('totalTokens')}</dt>
                          <dd className="text-2xl font-bold text-white">
                            {(() => {
                              const { value, unit } = formatTokens(metricsMap[apiKey.id].total_tokens, tStats('million'), tStats('tenThousand'));
                              return <>{value}<span className="text-sm font-normal text-[#b3b3b3] ml-1">{unit}</span></>;
                            })()}
                          </dd>
                        </div>
                        <div className="flex flex-col">
                          <dt className="text-xs font-semibold text-[#b3b3b3] mb-1">{tStats('totalDuration')}</dt>
                          <dd className="text-2xl font-bold text-white">
                            {metricsMap[apiKey.id].total_duration_days}<span className="text-sm font-normal text-[#b3b3b3] ml-1">{tStats('days')}</span>
                          </dd>
                        </div>
                        <div className="flex flex-col">
                          <dt className="text-xs font-semibold text-[#b3b3b3] mb-1">{tStats('totalRequests')}</dt>
                          <dd className="text-2xl font-bold text-white">
                            {metricsMap[apiKey.id].total_requests}<span className="text-sm font-normal text-[#b3b3b3] ml-1">{tStats('times')}</span>
                          </dd>
                        </div>
                      </dl>

                      {/* 48-hour Bar Chart */}
                      <div className="sm:flex-[3]  border border-[#282828] rounded-2xl overflow-hidden h-44 bg-[#181818] shadow-sm">
                        <div className="p-3 pt-2 pb-4 h-full">
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

      {/* Edit Subscription Dialog */}
      {editingApiKey && (
        <EditSubscriptionDialog
          apiKey={editingApiKey}
          onUpdated={loadSharedAPIKeys}
          open={editingApiKey !== null}
          onOpenChange={(open) => !open && setEditingApiKey(null)}
        />
      )}
    </div>
  );
}
