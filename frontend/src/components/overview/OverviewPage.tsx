'use client';

import { useEffect, useState, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { overviewAPI } from '@/lib/services';
import { useAuthStore } from '@/lib/store';
import { UsageStatsCard } from '@/components/usage/UsageStatsCard';
import { UsageBarChart } from '@/components/usage/UsageBarChart';
import { useToast } from '@/components/ui/toast';
import { useTranslations } from 'next-intl';

interface TrendData {
  time_slot: number;
  total_tokens: number;
}

// Alias for backward compatibility
type DailyTrendData = TrendData;

interface UserRankingData {
  user_id: number;
  user_name: string;
  consumed_tokens: number;
}

interface ClawRankingData {
  claw_id: number;
  claw_name: string;
  user_name: string;
  consumed_tokens: number;
}

interface SystemOverviewResponse {
  total_tokens: number;
  today_tokens: number;
  user_count: number;
  claw_count: number;
  daily_trends: DailyTrendData[];
  user_rankings: UserRankingData[];
  claw_rankings: ClawRankingData[];
}

// Time range options
const TIME_RANGE_OPTIONS = [
  { value: '1', label: '1' },
  { value: '7', label: '7' },
  { value: '30', label: '30' },
];

export function OverviewPage() {
  const t = useTranslations('overview');
  const tCommon = useTranslations('common');
  const { toast } = useToast();
  const { currentOrganization } = useAuthStore();

  // Time range state
  const [timeRange, setTimeRange] = useState<string>('7');

  // Data state
  const [overviewData, setOverviewData] = useState<SystemOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Load overview data
  const loadOverviewData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await overviewAPI.getSystemOverview({
        days: parseInt(timeRange),
        ...(currentOrganization && { org_id: currentOrganization.id })
      });
      setOverviewData(response.data);
    } catch (error) {
      setOverviewData(null);
      toast({
        title: tCommon('error'),
        description: t('error'),
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  }, [timeRange, currentOrganization, toast, t, tCommon]);

  // Load data on mount and when time range changes
  useEffect(() => {
    loadOverviewData();
  }, [loadOverviewData]);

  // Handle time range change
  const handleTimeRangeChange = (value: string) => {
    setTimeRange(value);
  };

  // Refresh data
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await loadOverviewData();
    } catch (error) {
      toast({
        title: tCommon('error'),
        description: t('error'),
        variant: 'destructive'
      });
    } finally {
      setIsRefreshing(false);
    }
  }, [loadOverviewData, toast, tCommon, t]);

  // Convert trend data to quarter-hourly format for bar chart
  const convertToChartFormat = (trends: TrendData[]) => {
    return trends.map(trend => ({
      quarter_hour: trend.time_slot,
      tokens: trend.total_tokens
    }));
  };

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <Card className=" border border-[#282828] bg-[#181818]">
        <CardHeader className="p-6">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div className="flex flex-col space-y-2">
              <h3 className="text-2xl font-bold text-white leading-none tracking-tight">{t('title')}</h3>
              <p className="text-sm text-[#b3b3b3] font-medium">{t('description')}</p>
            </div>
            {/* Refresh Button */}
            <Button
              variant="ghost"
              size="icon"
              className="text-[#b3b3b3] hover:text-[#b3b3b3] hover:bg-[#282828]"
              onClick={handleRefresh}
              disabled={isRefreshing}
              aria-label="刷新"
            >
              <RefreshCw className={`h-5 w-5 ${isRefreshing ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Loading state */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-[#b3b3b3] font-medium">{t('loading')}</div>
        </div>
      ) : overviewData === null ? (
        /* No data state */
        <div className="flex items-center justify-center py-12">
          <div className="text-[#b3b3b3] font-medium">{t('noData')}</div>
        </div>
      ) : (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <UsageStatsCard
              title={t('totalTokens')}
              value={overviewData.total_tokens.toLocaleString()}
            />
            <UsageStatsCard
              title={t('todayTokens')}
              value={overviewData.today_tokens.toLocaleString()}
            />
            <UsageStatsCard
              title={t('userCount')}
              value={overviewData.user_count}
            />
            <UsageStatsCard
              title={t('clawCount')}
              value={overviewData.claw_count}
            />
          </div>

          {/* Token Trend Chart - Full Width */}
          <Card className=" border border-[#282828] bg-[#181818]">
            <CardHeader className="p-6">
              <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
                <h4 className="text-lg font-bold text-white">{t('tokenTrend')}</h4>
                {/* Time Range Selector */}
                <div className="flex items-center gap-2">
                  <label className="text-sm font-medium text-[#b3b3b3] whitespace-nowrap">
                    {t('timeRange')}:
                  </label>
                  <Select value={timeRange} onValueChange={handleTimeRangeChange}>
                    <SelectTrigger className=" w-[140px] border border-[#282828]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {TIME_RANGE_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {t(`timeRanges.${option.value}`)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-6 pt-0">
              {overviewData.daily_trends.length > 0 ? (
                <div className=" border border-[#282828] rounded-2xl overflow-hidden h-64 bg-[#181818]">
                  <div className="p-4 h-full">
                    <UsageBarChart quarterHourlyDistribution={convertToChartFormat(overviewData.daily_trends)} days={parseInt(timeRange)} />
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-64 text-[#535353] text-sm">
                  {t('noData')}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Charts Row: Claw Rankings and User Rankings */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Claw Rankings */}
            <Card className=" border border-[#282828] bg-[#181818]">
              <CardHeader className="p-6">
                <h4 className="text-lg font-bold text-white">{t('clawRankings')}</h4>
              </CardHeader>
              <CardContent className="p-6 pt-0">
                {overviewData.claw_rankings.length > 0 ? (
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {overviewData.claw_rankings.map((claw, index) => (
                      <div
                        key={claw.claw_id}
                        className="flex items-center justify-between p-2.5 bg-[#282828] rounded-xl border border-[#282828]"
                      >
                        <div className="flex items-center gap-2">
                          <div className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs ${
                            index === 0 ? 'bg-[#ffa42b] text-[#121212]' :
                            index === 1 ? 'bg-[#535353] text-white' :
                            index === 2 ? 'bg-[#cd7f32] text-white' :
                            'bg-[#282828] text-[#b3b3b3]'
                          }`}>
                            {index + 1}
                          </div>
                          <span className="text-sm font-medium text-white">{claw.claw_name} ({claw.user_name})</span>
                        </div>
                        <span className="text-sm font-bold text-[#b3b3b3]">
                          {claw.consumed_tokens.toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-48 text-[#535353] text-sm">
                    {t('noData')}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* User Rankings */}
            <Card className=" border border-[#282828] bg-[#181818]">
              <CardHeader className="p-6">
                <h4 className="text-lg font-bold text-white">{t('userRankings')}</h4>
              </CardHeader>
              <CardContent className="p-6 pt-0">
                {overviewData.user_rankings.length > 0 ? (
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {overviewData.user_rankings.map((user, index) => (
                      <div
                        key={user.user_id}
                        className="flex items-center justify-between p-2.5 bg-[#282828] rounded-xl border border-[#282828]"
                      >
                        <div className="flex items-center gap-2">
                          <div className={`w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs ${
                            index === 0 ? 'bg-[#ffa42b] text-[#121212]' :
                            index === 1 ? 'bg-[#535353] text-white' :
                            index === 2 ? 'bg-[#cd7f32] text-white' :
                            'bg-[#282828] text-[#b3b3b3]'
                          }`}>
                            {index + 1}
                          </div>
                          <span className="text-sm font-medium text-white">{user.user_name}</span>
                        </div>
                        <span className="text-sm font-bold text-[#b3b3b3]">
                          {user.consumed_tokens.toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-48 text-[#535353] text-sm">
                    {t('noData')}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
