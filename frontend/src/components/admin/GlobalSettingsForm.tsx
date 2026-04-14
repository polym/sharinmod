'use client';

import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useTranslations } from 'next-intl';

interface GlobalSettingsFormProps {
  dailyTokenLimit: string;
  onChange: (field: 'dailyTokenLimit', value: string) => void;
}

export function GlobalSettingsForm({ dailyTokenLimit, onChange }: GlobalSettingsFormProps) {
  const t = useTranslations('adminSettings.global');

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="daily-token-limit">{t('dailyTokenLimit')}</Label>
        <Input
          id="daily-token-limit"
          type="number"
          min="1"
          value={dailyTokenLimit}
          onChange={(e) => onChange('dailyTokenLimit', e.target.value)}
        />
        <p className="text-xs text-[#b3b3b3]">{t('dailyTokenLimitDescription')}</p>
      </div>
    </div>
  );
}
