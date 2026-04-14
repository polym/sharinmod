'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/toast';
import { adminAPI } from '@/lib/services';
import { useTranslations } from 'next-intl';
import { Loader2 } from 'lucide-react';
import { GlobalSettingsForm } from './admin/GlobalSettingsForm';
import { ClawSettingsForm } from './admin/ClawSettingsForm';

// Helper: Convert hour (0-23) to cron expression "0 H * * *"
const hourToCron = (hour: number): string => {
  return `0 ${hour} * * *`;
};

// Helper: Extract hour from cron expression "0 H * * *"
const cronToHour = (cron: string): number => {
  const match = cron.match(/^0\s+(\d+)\s+\*\s+\*\s+\*\*$/);
  return match ? parseInt(match[1]) : 6; // Default to 6 (6:00) if invalid
};

export function AdminSettings() {
  const t = useTranslations('adminSettings');
  const tToast = useTranslations('adminSettings.toast');
  const { toast } = useToast();

  const [config, setConfig] = useState({
    default_daily_token_limit: '',
    max_claws_per_user: '',
    claw_apikey_daily_token_limit: '',
    claws_archive_enabled: false,
    claws_archive_auto_enabled: false,
    claws_archive_schedule_daily: '0 6 * * *',
    claws_archive_schedule_interval: 20,
    claws_archive_retention_daily: 1,
    claws_archive_retention_interval: 5,
    claws_archive_max_manual: 5,
    scheduleHour: 6 // Store hour separately for UI
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await adminAPI.getSystemSettingsConfig();
      const hour = cronToHour(response.data.claws_archive_schedule_daily);
      setConfig({
        default_daily_token_limit: response.data.default_daily_token_limit.toString(),
        max_claws_per_user: response.data.max_claws_per_user.toString(),
        claw_apikey_daily_token_limit: response.data.claw_apikey_daily_token_limit?.toString() || '',
        claws_archive_enabled: response.data.claws_archive_enabled,
        claws_archive_auto_enabled: response.data.claws_archive_auto_enabled,
        claws_archive_schedule_daily: response.data.claws_archive_schedule_daily,
        claws_archive_schedule_interval: response.data.claws_archive_schedule_interval,
        claws_archive_retention_daily: response.data.claws_archive_retention_daily,
        claws_archive_retention_interval: response.data.claws_archive_retention_interval,
        claws_archive_max_manual: response.data.claws_archive_max_manual,
        scheduleHour: hour
      });
    } catch (error) {
      console.error('Failed to load settings:', error);
      toast({
        title: tToast('loadError'),
        description: tToast('loadErrorDetail'),
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    // Validate database settings
    const dailyLimit = parseInt(config.default_daily_token_limit);
    const maxClaws = parseInt(config.max_claws_per_user);
    const clawLimit = config.claw_apikey_daily_token_limit ? parseInt(config.claw_apikey_daily_token_limit) : null;

    if (isNaN(dailyLimit) || dailyLimit <= 0 || isNaN(maxClaws) || maxClaws <= 0 ||
        (clawLimit !== null && (isNaN(clawLimit) || clawLimit <= 0))) {
      toast({
        title: tToast('invalidValue'),
        description: tToast('invalidValueDetail'),
        variant: 'destructive',
      });
      return;
    }

    // Validate numeric fields with range limits
    const scheduleInterval = config.claws_archive_schedule_interval;
    const retentionDaily = config.claws_archive_retention_daily;
    const retentionInterval = config.claws_archive_retention_interval;
    const maxManual = config.claws_archive_max_manual;

    // Validate schedule interval: 5-1440 minutes
    if (isNaN(scheduleInterval) || scheduleInterval < 5 || scheduleInterval > 1440) {
      toast({
        title: tToast('invalidNumber'),
        description: '间隔备份分钟数必须在 5 到 1440 之间',
        variant: 'destructive',
      });
      return;
    }

    // Validate retention daily: 1-365
    if (isNaN(retentionDaily) || retentionDaily < 1 || retentionDaily > 365) {
      toast({
        title: tToast('invalidNumber'),
        description: '每日备份保留数量必须在 1 到 365 之间',
        variant: 'destructive',
      });
      return;
    }

    // Validate retention interval: 1-168
    if (isNaN(retentionInterval) || retentionInterval < 1 || retentionInterval > 168) {
      toast({
        title: tToast('invalidNumber'),
        description: '间隔备份保留数量必须在 1 到 168 之间',
        variant: 'destructive',
      });
      return;
    }

    // Validate max manual: 1-100
    if (isNaN(maxManual) || maxManual < 1 || maxManual > 100) {
      toast({
        title: tToast('invalidNumber'),
        description: '手动备份最大数量必须在 1 到 100 之间',
        variant: 'destructive',
      });
      return;
    }

    // Convert hour to cron expression before saving
    const cronExpression = hourToCron(config.scheduleHour);

    setSaving(true);
    try {
      await adminAPI.updateSystemSettingsConfig({
        default_daily_token_limit: dailyLimit,
        max_claws_per_user: maxClaws,
        claw_apikey_daily_token_limit: clawLimit,
        claws_archive_enabled: config.claws_archive_enabled,
        claws_archive_auto_enabled: config.claws_archive_auto_enabled,
        claws_archive_schedule_daily: cronExpression,
        claws_archive_schedule_interval: scheduleInterval,
        claws_archive_retention_daily: retentionDaily,
        claws_archive_retention_interval: retentionInterval,
        claws_archive_max_manual: maxManual
      });
      toast({
        title: tToast('saveSuccess'),
        description: tToast('saveSuccessDetail'),
      });
    } catch (error: any) {
      toast({
        title: tToast('saveError'),
        description: error.response?.data?.detail || tToast('saveErrorDetail'),
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleGlobalChange = (field: 'dailyTokenLimit', value: string) => {
    if (field === 'dailyTokenLimit') {
      setConfig({ ...config, default_daily_token_limit: value });
    }
  };

  const handleClawChange = (field: string, value: any) => {
    const fieldMap: Record<string, string> = {
      maxCount: 'max_claws_per_user',
      dailyTokenLimit: 'claw_apikey_daily_token_limit',
      archiveEnabled: 'claws_archive_enabled',
      autoEnabled: 'claws_archive_auto_enabled',
      retentionDaily: 'claws_archive_retention_daily',
      scheduleInterval: 'claws_archive_schedule_interval',
      retentionInterval: 'claws_archive_retention_interval',
      maxManual: 'claws_archive_max_manual',
      scheduleHour: 'scheduleHour'
    };

    const configField = fieldMap[field];
    if (configField) {
      setConfig({ ...config, [configField]: value });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-[#b3b3b3]" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Tabs defaultValue="global">
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>{t('title')}</CardTitle>
                <CardDescription>{t('description')}</CardDescription>
              </div>
              <TabsList>
                <TabsTrigger value="global">{t('tabs.global')}</TabsTrigger>
                <TabsTrigger value="claw">{t('tabs.claw')}</TabsTrigger>
              </TabsList>
            </div>
          </CardHeader>
          <CardContent>
            <TabsContent value="global" className="mt-0">
              <GlobalSettingsForm
                dailyTokenLimit={config.default_daily_token_limit}
                onChange={handleGlobalChange}
              />
            </TabsContent>
            <TabsContent value="claw" className="mt-0">
              <ClawSettingsForm
                maxCount={config.max_claws_per_user}
                dailyTokenLimit={config.claw_apikey_daily_token_limit}
                archiveEnabled={config.claws_archive_enabled}
                autoEnabled={config.claws_archive_auto_enabled}
                scheduleHour={config.scheduleHour}
                retentionDaily={config.claws_archive_retention_daily}
                scheduleInterval={config.claws_archive_schedule_interval}
                retentionInterval={config.claws_archive_retention_interval}
                maxManual={config.claws_archive_max_manual}
                onChange={handleClawChange}
              />
            </TabsContent>
          </CardContent>
          <CardFooter className="flex justify-end">
            <Button onClick={handleSave} disabled={saving}>
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              {saving ? t('saving') : t('save')}
            </Button>
          </CardFooter>
        </Card>
      </Tabs>
    </div>
  );
}