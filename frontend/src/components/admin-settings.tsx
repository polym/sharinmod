'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/components/ui/toast';
import { adminAPI } from '@/lib/services';
import { useTranslations } from 'next-intl';
import { Loader2 } from 'lucide-react';

export function AdminSettings() {
  const t = useTranslations('adminSettings');
  const tToast = useTranslations('adminSettings.toast');
  const tArchive = useTranslations('adminSettings.archiveConfig');
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
    claws_archive_max_manual: 5
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await adminAPI.getSystemSettingsConfig();
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
        claws_archive_max_manual: response.data.claws_archive_max_manual
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

    // Validate cron expression
    const cronPattern = /^\S+\s+\S+\s+\S+\s+\S+\s+\S+$/;
    if (!cronPattern.test(config.claws_archive_schedule_daily)) {
      toast({
        title: tToast('invalidCron'),
        description: tToast('saveErrorDetail'),
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

    setSaving(true);
    try {
      await adminAPI.updateSystemSettingsConfig({
        default_daily_token_limit: dailyLimit,
        max_claws_per_user: maxClaws,
        claw_apikey_daily_token_limit: clawLimit,
        claws_archive_enabled: config.claws_archive_enabled,
        claws_archive_auto_enabled: config.claws_archive_auto_enabled,
        claws_archive_schedule_daily: config.claws_archive_schedule_daily,
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

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-900">{t('title')}</h1>

      <Card className="border border-gray-200">
        <CardHeader>
          <CardTitle className="text-lg">系统限制配置</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="daily-limit">{t('apikeyLimit.dailyLimit')}</Label>
            <Input
              id="daily-limit"
              type="number"
              min="1"
              value={config.default_daily_token_limit}
              onChange={(e) => setConfig({ ...config, default_daily_token_limit: e.target.value })}
              className="max-w-xs"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="max-claws">{t('clawLimit.maxClaws')}</Label>
            <Input
              id="max-claws"
              type="number"
              min="1"
              value={config.max_claws_per_user}
              onChange={(e) => setConfig({ ...config, max_claws_per_user: e.target.value })}
              className="max-w-xs"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="claw-limit">{t('clawApikeyLimit.dailyLimit')}</Label>
            <Input
              id="claw-limit"
              type="number"
              min="1"
              value={config.claw_apikey_daily_token_limit}
              onChange={(e) => setConfig({ ...config, claw_apikey_daily_token_limit: e.target.value })}
              className="max-w-xs"
              placeholder={t('clawApikeyLimit.placeholder')}
            />
            <p className="text-xs text-gray-500">{t('clawApikeyLimit.placeholder')}</p>
          </div>
        </CardContent>
      </Card>

      <Card className="border border-gray-200">
        <CardHeader>
          <CardTitle className="text-lg">{tArchive('title')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="archive-enabled">{tArchive('enabled')}</Label>
              <p className="text-xs text-gray-500">{tArchive('description')}</p>
            </div>
            <Switch
              id="archive-enabled"
              checked={config.claws_archive_enabled}
              onCheckedChange={(checked) => setConfig({ ...config, claws_archive_enabled: checked })}
            />
          </div>

          <div className="flex items-center justify-between">
            <Label htmlFor="auto-enabled">{tArchive('autoEnabled')}</Label>
            <Switch
              id="auto-enabled"
              checked={config.claws_archive_auto_enabled}
              onCheckedChange={(checked) => setConfig({ ...config, claws_archive_auto_enabled: checked })}
              disabled={!config.claws_archive_enabled}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="schedule-daily">{tArchive('scheduleDaily')}</Label>
            <Input
              id="schedule-daily"
              type="text"
              value={config.claws_archive_schedule_daily}
              onChange={(e) => setConfig({ ...config, claws_archive_schedule_daily: e.target.value })}
              className="max-w-xs"
              placeholder={tArchive('scheduleDailyPlaceholder')}
              disabled={!config.claws_archive_enabled}
            />
            <p className="text-xs text-gray-500">{tArchive('scheduleDailyHint')}</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="schedule-interval">{tArchive('scheduleInterval')}</Label>
            <Input
              id="schedule-interval"
              type="number"
              min="5"
              max="1440"
              value={config.claws_archive_schedule_interval}
              onChange={(e) => setConfig({ ...config, claws_archive_schedule_interval: parseInt(e.target.value) || 5 })}
              className="max-w-xs"
              placeholder={tArchive('scheduleIntervalPlaceholder')}
              disabled={!config.claws_archive_enabled}
            />
            <p className="text-xs text-gray-500">{tArchive('scheduleIntervalHint')} (5-1440)</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="retention-daily">{tArchive('retentionDaily')}</Label>
            <Input
              id="retention-daily"
              type="number"
              min="1"
              max="365"
              value={config.claws_archive_retention_daily}
              onChange={(e) => setConfig({ ...config, claws_archive_retention_daily: parseInt(e.target.value) || 1 })}
              className="max-w-xs"
              placeholder={tArchive('retentionDailyPlaceholder')}
              disabled={!config.claws_archive_enabled}
            />
            <p className="text-xs text-gray-500">{tArchive('retentionDailyHint')} (1-365)</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="retention-interval">{tArchive('retentionInterval')}</Label>
            <Input
              id="retention-interval"
              type="number"
              min="1"
              max="168"
              value={config.claws_archive_retention_interval}
              onChange={(e) => setConfig({ ...config, claws_archive_retention_interval: parseInt(e.target.value) || 1 })}
              className="max-w-xs"
              placeholder={tArchive('retentionIntervalPlaceholder')}
              disabled={!config.claws_archive_enabled}
            />
            <p className="text-xs text-gray-500">{tArchive('retentionIntervalHint')} (1-168)</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="max-manual">{tArchive('maxManual')}</Label>
            <Input
              id="max-manual"
              type="number"
              min="1"
              max="100"
              value={config.claws_archive_max_manual}
              onChange={(e) => setConfig({ ...config, claws_archive_max_manual: parseInt(e.target.value) || 1 })}
              className="max-w-xs"
              placeholder={tArchive('maxManualPlaceholder')}
              disabled={!config.claws_archive_enabled}
            />
            <p className="text-xs text-gray-500">{tArchive('maxManualHint')}</p>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
          {saving ? t('saving') : t('save')}
        </Button>
      </div>
    </div>
  );
}