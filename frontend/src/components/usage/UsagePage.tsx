'use client';

import { useEffect, useState, useCallback, useMemo } from 'react';
import { RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { usageAPI, apiKeyAPI } from '@/lib/services';
import { UsageStatsCard } from './UsageStatsCard';
import { UsageBarChart } from './UsageBarChart';
import { UsageLogsTable } from './UsageLogsTable';
import { useToast } from '@/components/ui/toast';
import { useTranslations } from 'next-intl';

interface UnifiedAPIKey {
  id: number;
  api_key_name: string;
  litellm_key?: string;
}

interface UsageOverview {
  date: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  total_tokens: number;
  input_tokens: number;
  output_tokens: number;
  quarter_hourly_distribution: Array<{ quarter_hour: number; tokens: number }>;
}

interface UsageLog {
  id: number;
  request_time: string;
  model_name: string;
  status: string;
  kind: string;
  unified_api_key_name: string | null;
  client: string | null;
  total_tokens: number;
  input_tokens: number;
  output_tokens: number;
  ttft: number | null;
  total_duration: number | null;
  num_fails: number;
}

interface UsageLogsResponse {
  total: number;
  page: number;
  page_size: number;
  items: UsageLog[];
}

export function UsagePage() {
  const t = useTranslations('usage');
  const tCommon = useTranslations('common');
  const { toast } = useToast();

  // Get user timezone
  const [userTimezone] = useState<string>(() =>
    Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Shanghai'
  );

  // Filter state - default to today in user's timezone
  const [selectedDate, setSelectedDate] = useState<string>(() => {
    const now = new Date();
    // Format date as YYYY-MM-DD in user's local timezone
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  });
  const [selectedApiKey, setSelectedApiKey] = useState<string>('all');

  // API Keys state
  const [apiKeys, setApiKeys] = useState<UnifiedAPIKey[]>([]);
  const [apiKeysLoading, setApiKeysLoading] = useState(true);

  // Overview data state
  const [overviewData, setOverviewData] = useState<UsageOverview | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(true);

  // Logs data state
  const [logsData, setLogsData] = useState<UsageLog[]>([]);
  const [logsPage, setLogsPage] = useState(1);
  const [logsTotal, setLogsTotal] = useState(0);
  const [logsLoading, setLogsLoading] = useState(false);
  const [hasMoreLogs, setHasMoreLogs] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const PAGE_SIZE = 20;

  // Generate last 7 days options
  const dateOptions = useMemo(() => {
    return Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - i);
      return date;
    });
  }, []);

  // Format date label as "YYYY/MM/DD"
  const formatDateLabel = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}/${month}/${day}`;
  };

  // Format date as YYYY-MM-DD for value
  const formatDateValue = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Load API Keys
  const loadAPIKeys = useCallback(async () => {
    try {
      setApiKeysLoading(true);
      const response = await apiKeyAPI.getMyUnifiedAPIKeysIncludeAutoCreated();
      setApiKeys(response.data.items);
    } catch (error) {
      console.error('Failed to load API keys:', error);
    } finally {
      setApiKeysLoading(false);
    }
  }, []);

  // Load overview data
  const loadOverviewData = useCallback(async () => {
    try {
      setOverviewLoading(true);
      const response = await usageAPI.getOverview({
        target_date: selectedDate,
        ...(selectedApiKey !== 'all' && { unified_api_key_id: parseInt(selectedApiKey) })
      });
      setOverviewData(response.data);
    } catch (error) {
      console.error('Failed to load overview data:', error);
      setOverviewData(null);
    } finally {
      setOverviewLoading(false);
    }
  }, [selectedDate, selectedApiKey]);

  // Load logs data
  const loadLogsData = useCallback(async (page: number, reset: boolean = false) => {
    try {
      setLogsLoading(true);
      const response = await usageAPI.getLogs({
        page,
        page_size: PAGE_SIZE,
        start_date: selectedDate,
        end_date: selectedDate,
        ...(selectedApiKey !== 'all' && { unified_api_key_id: parseInt(selectedApiKey) })
      });

      const data = response.data as UsageLogsResponse;

      if (reset) {
        setLogsData(data.items);
        setLogsPage(1);
      } else {
        setLogsData(prev => [...prev, ...data.items]);
        setLogsPage(page);
      }

      setLogsTotal(data.total);
      setHasMoreLogs(data.items.length === PAGE_SIZE);
    } catch (error) {
      console.error('Failed to load logs data:', error);
      if (reset) {
        setLogsData([]);
      }
    } finally {
      setLogsLoading(false);
    }
  }, [selectedDate, selectedApiKey]);

  // Load API Keys on mount
  useEffect(() => {
    loadAPIKeys();
  }, [loadAPIKeys]);

  // Load overview data when date changes
  useEffect(() => {
    loadOverviewData();
  }, [loadOverviewData]);

  // Load logs data when date or API key filter changes
  useEffect(() => {
    loadLogsData(1, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate, selectedApiKey]);

  const handleLoadMore = () => {
    loadLogsData(logsPage + 1, false);
  };

  const handleDateChange = (value: string) => {
    setSelectedDate(value);
  };

  const handleApiKeyChange = (value: string) => {
    setSelectedApiKey(value);
  };

  // Refresh all data
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        loadAPIKeys(),
        loadOverviewData(),
        loadLogsData(1, true)
      ]);
    } catch (error) {
      console.error('Failed to refresh data:', error);
      toast({
        title: tCommon('error'),
        description: t('refreshFailed'),
        variant: 'destructive'
      });
    } finally {
      setIsRefreshing(false);
    }
  }, [loadAPIKeys, loadOverviewData, loadLogsData, toast, tCommon, t]);

  // Token formatting helper
  const formatTokenValue = (total: number, input: number, output: number) => {
    return `${total.toLocaleString()} (${input.toLocaleString()} + ${output.toLocaleString()})`;
  };

  return (
    <Card>
      <CardHeader className="p-6">
        <div className="flex justify-between items-center">
          <div className="flex flex-col space-y-1.5">
            <CardTitle>{t('title')}</CardTitle>
            <CardDescription>{t('description')}</CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            {/* Date Filter */}
            <Select value={selectedDate} onValueChange={handleDateChange}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder={t('selectDatePlaceholder')} />
              </SelectTrigger>
              <SelectContent>
                {dateOptions.map((date) => (
                  <SelectItem key={formatDateValue(date)} value={formatDateValue(date)}>
                    {formatDateLabel(date)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* API Key Filter */}
            <Select value={selectedApiKey} onValueChange={handleApiKeyChange} disabled={apiKeysLoading}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder={t('selectApiKeyPlaceholder')} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t('all')}</SelectItem>
                {apiKeys.map((key) => (
                  <SelectItem key={key.id} value={key.id.toString()}>
                    {key.api_key_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Refresh Button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={handleRefresh}
              disabled={isRefreshing}
              aria-label={t('refresh')}
            >
              <RefreshCw className={`h-5 w-5 ${isRefreshing ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Loading state */}
        {overviewLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-gray-600 font-medium">{tCommon('loading')}</div>
          </div>
        ) : overviewData === null ? (
          /* No data state */
          <div className="flex items-center justify-center py-12">
            <div className="text-gray-600 font-medium">{t('noData')}</div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <UsageStatsCard
                title={t('totalTokens')}
                value={overviewData.total_tokens.toLocaleString()}
              />
              <UsageStatsCard
                title={t('inputTokens')}
                value={overviewData.input_tokens.toLocaleString()}
              />
              <UsageStatsCard
                title={t('outputTokens')}
                value={overviewData.output_tokens.toLocaleString()}
              />
              <UsageStatsCard
                title={t('totalRequests')}
                value={`${overviewData.successful_requests + overviewData.failed_requests}`}
                subtitle={`${overviewData.successful_requests} ${t('successfulRequests')} + ${overviewData.failed_requests} ${t('failedRequests')}`}
              />
            </div>

            {/* Hourly Distribution Chart */}
            <div className="space-y-2">
              <h4 className="text-lg font-semibold">{t('tokenDistribution')}</h4>
              <div className="border rounded-lg overflow-hidden h-40 bg-white overflow-x-auto">
                <div className="p-2 pt-2 pb-5 h-full min-w-[850px]">
                  <UsageBarChart quarterHourlyDistribution={overviewData.quarter_hourly_distribution} />
                </div>
              </div>
            </div>

            {/* Usage Logs Table */}
            <div className="space-y-2">
              <h4 className="text-lg font-semibold">{t('detailedRecords')}</h4>
              {logsData.length === 0 && !logsLoading ? (
                <div className="text-center py-8 text-gray-600 font-medium">
                  {t('noRecords')}
                </div>
              ) : (
                <UsageLogsTable
                  logs={logsData}
                  hasMore={hasMoreLogs}
                  onLoadMore={handleLoadMore}
                  loading={logsLoading}
                  userTimezone={userTimezone}
                />
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
