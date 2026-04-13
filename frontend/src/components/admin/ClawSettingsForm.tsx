'use client';

import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useTranslations } from 'next-intl';

interface ClawSettingsFormProps {
  maxCount: string;
  dailyTokenLimit: string;
  archiveEnabled: boolean;
  autoEnabled: boolean;
  scheduleHour: number;
  retentionDaily: number;
  scheduleInterval: number;
  retentionInterval: number;
  maxManual: number;
  onChange: (field: string, value: any) => void;
}

export function ClawSettingsForm({
  maxCount,
  dailyTokenLimit,
  archiveEnabled,
  autoEnabled,
  scheduleHour,
  retentionDaily,
  scheduleInterval,
  retentionInterval,
  maxManual,
  onChange
}: ClawSettingsFormProps) {
  const t = useTranslations('adminSettings.claw');

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="max-count">{t('maxCount')}</Label>
          <Input
            id="max-count"
            type="number"
            min="1"
            value={maxCount}
            onChange={(e) => onChange('maxCount', e.target.value)}
          />
          <p className="text-xs text-gray-500">{t('maxCountDescription')}</p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="claw-daily-token-limit">{t('dailyTokenLimit')}</Label>
          <Input
            id="claw-daily-token-limit"
            type="number"
            min="1"
            value={dailyTokenLimit}
            onChange={(e) => onChange('dailyTokenLimit', e.target.value)}
            placeholder={t('placeholder')}
          />
          <p className="text-xs text-gray-500">{t('dailyTokenLimitDescription')}</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex-1">
          <Label htmlFor="archive-enabled">{t('archive.enabled')}</Label>
          <p className="text-xs text-gray-500">{t('archive.description')}</p>
        </div>
        <Switch
          id="archive-enabled"
          checked={archiveEnabled}
          onCheckedChange={(checked) => onChange('archiveEnabled', checked)}
        />
      </div>

      {archiveEnabled && (
        <div className="space-y-2">
          <Label htmlFor="max-manual">{t('archive.maxManual')}</Label>
          <Input
            id="max-manual"
            type="number"
            min="1"
            max="100"
            value={maxManual}
            onChange={(e) => onChange('maxManual', parseInt(e.target.value) || 1)}
          />
        </div>
      )}

      {archiveEnabled && (
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <Label htmlFor="auto-enabled">{t('archive.autoEnabled')}</Label>
          </div>
          <Switch
            id="auto-enabled"
            checked={autoEnabled}
            onCheckedChange={(checked) => onChange('autoEnabled', checked)}
          />
        </div>
      )}

      {/* 每日备份配置 - 双列 */}
      {archiveEnabled && autoEnabled && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="schedule-hour">{t('archive.scheduleDaily')}</Label>
            <Select
              value={scheduleHour.toString()}
              onValueChange={(value) => onChange('scheduleHour', parseInt(value))}
            >
              <SelectTrigger id="schedule-hour">
                <SelectValue placeholder={t('archive.scheduleDailyPlaceholder')} />
              </SelectTrigger>
              <SelectContent>
                {Array.from({ length: 24 }, (_, i) => (
                  <SelectItem key={i} value={i.toString()}>
                    {t(`archive.hours.${i}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="retention-daily">{t('archive.retentionDaily')}</Label>
            <Input
              id="retention-daily"
              type="number"
              min="1"
              max="365"
              value={retentionDaily}
              onChange={(e) => onChange('retentionDaily', parseInt(e.target.value) || 1)}
            />
          </div>
        </div>
      )}

      {/* 间隔备份配置 - 双列 */}
      {archiveEnabled && autoEnabled && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="schedule-interval">{t('archive.scheduleInterval')}</Label>
            <Input
              id="schedule-interval"
              type="number"
              min="5"
              max="1440"
              value={scheduleInterval}
              onChange={(e) => onChange('scheduleInterval', parseInt(e.target.value) || 5)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="retention-interval">{t('archive.retentionInterval')}</Label>
            <Input
              id="retention-interval"
              type="number"
              min="1"
              max="168"
              value={retentionInterval}
              onChange={(e) => onChange('retentionInterval', parseInt(e.target.value) || 1)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
