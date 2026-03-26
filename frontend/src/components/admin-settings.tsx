'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/toast';
import { adminAPI } from '@/lib/services';
import { useTranslations } from 'next-intl';
import { Loader2 } from 'lucide-react';

export function AdminSettings() {
  const t = useTranslations('adminSettings');
  const tToast = useTranslations('adminSettings.toast');
  const { toast } = useToast();

  const [config, setConfig] = useState({
    default_daily_token_limit: '',
    max_claws_per_user: '',
    claw_apikey_daily_token_limit: ''
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
        claw_apikey_daily_token_limit: response.data.claw_apikey_daily_token_limit?.toString() || ''
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

    setSaving(true);
    try {
      await adminAPI.updateSystemSettingsConfig({
        default_daily_token_limit: dailyLimit,
        max_claws_per_user: maxClaws,
        claw_apikey_daily_token_limit: clawLimit
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
      <div>
        <h1 className="text-3xl font-bold text-gray-900">{t('title')}</h1>
        <p className="text-gray-600 mt-2">{t('description')}</p>
      </div>

      <Card className="clay-card border-2 border-indigo-100">
        <CardHeader>
          <CardTitle>{t('configTitle')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* APIKey 每日限额 */}
          <div className="grid grid-cols-[200px_1fr] items-center gap-4">
            <Label htmlFor="daily-limit">{t('apikeyLimit.dailyLimit')}</Label>
            <Input
              id="daily-limit"
              type="number"
              min="1"
              value={config.default_daily_token_limit}
              onChange={(e) => setConfig({ ...config, default_daily_token_limit: e.target.value })}
              className="clay-input max-w-md"
            />
          </div>

          {/* 最大龙虾数量 */}
          <div className="grid grid-cols-[200px_1fr] items-center gap-4">
            <Label htmlFor="max-claws">{t('clawLimit.maxClaws')}</Label>
            <Input
              id="max-claws"
              type="number"
              min="1"
              value={config.max_claws_per_user}
              onChange={(e) => setConfig({ ...config, max_claws_per_user: e.target.value })}
              className="clay-input max-w-md"
            />
          </div>

          {/* 龙虾 APIKey 限额 */}
          <div className="grid grid-cols-[200px_1fr] items-center gap-4">
            <Label htmlFor="claw-limit">{t('clawApikeyLimit.dailyLimit')}</Label>
            <Input
              id="claw-limit"
              type="number"
              min="1"
              value={config.claw_apikey_daily_token_limit}
              onChange={(e) => setConfig({ ...config, claw_apikey_daily_token_limit: e.target.value })}
              className="clay-input max-w-md"
              placeholder={t('clawApikeyLimit.placeholder')}
            />
          </div>

          <div className="flex justify-end pt-4 border-t">
            <Button onClick={handleSave} disabled={saving} className="clay-btn-primary">
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              {saving ? t('saving') : t('save')}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}