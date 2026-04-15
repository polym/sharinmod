'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/lib/store';
import { UsagePage } from '@/components/usage/UsagePage';
import { useTranslations } from 'next-intl';

export default function UsagePageRoute() {
  const [isHydrated, setIsHydrated] = useState(false);
  const { isAuthenticated, setShowLoginDialog } = useAuthStore();
  const t = useTranslations('common');

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (!isHydrated) return;

    if (!isAuthenticated) {
      setShowLoginDialog(true);
      return;
    }
  }, [isAuthenticated, setShowLoginDialog, isHydrated]);

  if (!isHydrated || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#121212] flex items-center justify-center">
        <div className="text-[#b3b3b3]">{t('loading')}</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-8 space-y-6">
      <UsagePage />
    </div>
  );
}
