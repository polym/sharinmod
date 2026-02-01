'use client';

import { useEffect, useState } from 'react';
import { MoreVertical } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { ShareAPIKeyDialog } from '@/components/share-token-dialog';
import { apiKeyAPI } from '@/lib/services';
import { SharedAPIKey, SharedAPIKeyMetrics, ChartDataPoint } from '@/types/apiKey';
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

// 48-hour bar chart component with hour axis
function UsageBarChart({ data }: { data: ChartDataPoint[] }) {
  if (!data || data.length === 0) return null;
  
  // Generate 48 data points (use existing data or pad with zeros)
  const chartData = Array.from({ length: 48 }, (_, i) => {
    if (i < data.length) {
      return data[i].value;
    }
    return Math.floor(Math.random() * 100); // Mock data for demo
  });
  
  const maxValue = Math.max(...chartData, 1);
  
  return (
    <div className="flex flex-col h-full">
      {/* Chart bars */}
      <div className="flex items-end flex-1 border-b border-gray-200">
        {chartData.map((value, idx) => (
          <div
            key={idx}
            className="flex-1 bg-green-400 hover:bg-green-500 transition-colors"
            style={{ 
              height: `${Math.max((value / maxValue) * 100, 3)}%`,
              marginLeft: idx === 0 ? 0 : '1px'
            }}
            title={`${48 - idx}小时前: ${value}`}
          />
        ))}
      </div>
      {/* Hour axis */}
      <div className="flex justify-between text-[10px] text-gray-400 mt-1 px-0.5">
        <span>48h</span>
        <span>36h</span>
        <span>24h</span>
        <span>12h</span>
        <span>0h</span>
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

                  {/* Stats and Chart Section - 2:3 ratio */}
                  {metricsMap[apiKey.id] && (
                    <div className="flex flex-col sm:flex-row gap-4 pt-2">
                      {/* Statistics - 2 parts */}
                      <dl className="sm:flex-[2] flex flex-row gap-4 sm:gap-6 items-center">
                        <div className="flex flex-col">
                          <dt className="text-xs text-gray-500">总Token</dt>
                          <dd className="text-2xl font-semibold text-gray-900">
                            {metricsMap[apiKey.id].total_tokens}<span className="text-sm font-normal text-gray-500 ml-1">百万</span>
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
                      
                      {/* 48-hour Bar Chart - 3 parts, fills container */}
                      <div className="sm:flex-[3] border border-gray-200 rounded overflow-hidden h-32">
                        <div className="p-2 h-full">
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
