'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/toast';
import { adminAPI } from '@/lib/services';
import { useTranslations } from 'next-intl';
import { Loader2 } from 'lucide-react';

export function AdminSettings() {
  const t = useTranslations('adminSettings');
  const tToast = useTranslations('adminSettings.toast');
  const { toast } = useToast();

  const [dailyTokenLimit, setDailyTokenLimit] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await adminAPI.getDefaultDailyTokenLimit();
      setDailyTokenLimit(response.data.toString());
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

  const handleSaveDailyTokenLimit = async () => {
    if (!dailyTokenLimit || parseInt(dailyTokenLimit) <= 0) {
      toast({
        title: tToast('invalidValue'),
        description: tToast('invalidValueDetail'),
        variant: 'destructive',
      });
      return;
    }

    setSaving(true);
    try {
      await adminAPI.updateDefaultDailyTokenLimit(dailyTokenLimit);
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">{t('title')}</h1>
        <p className="text-gray-600 mt-2">{t('description')}</p>
      </div>

      <Tabs defaultValue="apikey-limit" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-1">
          <TabsTrigger value="apikey-limit">{t('tabs.apikeyLimit')}</TabsTrigger>
        </TabsList>

        <TabsContent value="apikey-limit" className="space-y-6">
          <Card className="clay-card border-[3px] border-indigo-100 bg-gradient-to-br from-white to-indigo-50/30">
            <CardHeader className="p-6">
              <CardTitle className="text-2xl font-bold text-indigo-900">{t('apikeyLimit.title')}</CardTitle>
              <CardDescription className="text-indigo-600 font-medium">
                {t('apikeyLimit.description')}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-indigo-600" />
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="daily-token-limit" className="text-right text-indigo-700 font-medium">
                      {t('apikeyLimit.dailyLimit')}
                    </Label>
                    <div className="col-span-3 space-y-2">
                      <Input
                        id="daily-token-limit"
                        type="number"
                        min="1"
                        value={dailyTokenLimit}
                        onChange={(e) => setDailyTokenLimit(e.target.value)}
                        className="clay-input border-2 border-indigo-200/50"
                        placeholder={t('apikeyLimit.placeholder')}
                      />
                      <p className="text-sm text-indigo-500">{t('apikeyLimit.hint')}</p>
                    </div>
                  </div>

                  <div className="flex justify-end pt-4">
                    <Button
                      onClick={handleSaveDailyTokenLimit}
                      disabled={saving}
                      className="clay-btn-primary"
                    >
                      {saving ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          {t('saving')}
                        </>
                      ) : (
                        t('save')
                      )}
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
