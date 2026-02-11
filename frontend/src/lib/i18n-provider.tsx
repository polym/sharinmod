'use client';

import { NextIntlClientProvider } from 'next-intl';
import { useLocaleStore } from '@/lib/store';
import type { Locale } from '@/i18n';
import { useEffect, useState } from 'react';

type Messages = typeof import('@/messages/zh-CN.json');

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const { locale, setLocale } = useLocaleStore();
  const [messages, setMessages] = useState<Messages | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    // Ensure locale is set after hydration
    if (!locale) {
      const storedLocale = localStorage.getItem('sharinmod-locale');
      if (storedLocale) {
        const parsed = JSON.parse(storedLocale);
        if (parsed.state && parsed.state.locale) {
          setLocale(parsed.state.locale);
        }
      }
    }
    setIsHydrated(true);
  }, [locale, setLocale]);

  useEffect(() => {
    if (!locale) return;

    const loadMessages = async () => {
      try {
        let newMessages: Messages;
        if (locale === 'zh-CN') {
          newMessages = await import('@/messages/zh-CN.json');
        } else {
          newMessages = await import('@/messages/en.json');
        }
        setMessages(newMessages);
      } catch (error) {
        console.error('Failed to load messages:', error);
        // Fallback to Chinese messages
        const fallbackMessages = await import('@/messages/zh-CN.json');
        setMessages(fallbackMessages);
      }
    };

    loadMessages();
  }, [locale]);

  // Avoid flash of untranslated content - wait for hydration and messages
  if (!isHydrated || !messages || !locale) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      {children}
    </NextIntlClientProvider>
  );
}
