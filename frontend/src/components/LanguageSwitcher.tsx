'use client';

import { localeNames, type Locale } from '@/i18n';
import { useLocaleStore } from '@/lib/store';
import { useTranslations } from 'next-intl';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Globe } from 'lucide-react';

export function LanguageSwitcher() {
  const { locale, setLocale } = useLocaleStore();
  const t = useTranslations('settings');

  return (
    <div className="flex items-center gap-2">
      <Globe className="w-4 h-4 text-gray-500" />
      <Select
        value={locale}
        onValueChange={(value: Locale) => setLocale(value)}
      >
        <SelectTrigger className="w-[120px]">
          <SelectValue placeholder={t('language')} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="zh-CN">{localeNames['zh-CN']}</SelectItem>
          <SelectItem value="en">{localeNames['en']}</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
