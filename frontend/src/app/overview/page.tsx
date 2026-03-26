'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/lib/store';
import { OverviewPage } from '@/components/overview/OverviewPage';

export default function OverviewPageRoute() {
  const [isHydrated, setIsHydrated] = useState(false);
  const { isAuthenticated, setShowLoginDialog } = useAuthStore();

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
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-indigo-600 font-medium">加载中...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-8">
      <OverviewPage />
    </div>
  );
}
