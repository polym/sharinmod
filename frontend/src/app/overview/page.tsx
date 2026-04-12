'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { OverviewPage } from '@/components/overview/OverviewPage';
import { useTranslations } from 'next-intl';

export default function OverviewPageRoute() {
  const router = useRouter();
  const [isHydrated, setIsHydrated] = useState(false);
  const { isAuthenticated, setShowLoginDialog, currentOrganization, myOrganizations } = useAuthStore();
  const t = useTranslations('common');

  // Check if user is org owner
  const isOrgOwner = currentOrganization && myOrganizations?.owned.some(org => org.id === currentOrganization.id);
  const hasAccess = !currentOrganization || isOrgOwner;

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (!isHydrated) return;

    if (!isAuthenticated) {
      setShowLoginDialog(true);
      return;
    }

    // Redirect to usage page if user doesn't have access to overview
    if (!hasAccess) {
      router.push('/usage');
      return;
    }
  }, [isAuthenticated, hasAccess, isHydrated, router, setShowLoginDialog]);

  if (!isHydrated || !isAuthenticated || !hasAccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-indigo-600 font-medium">{t('loading')}</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-8">
      <OverviewPage />
    </div>
  );
}
