'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { MarketplacePage } from '@/components/MarketplacePage';

export default function MarketplaceRoute() {
  const [isHydrated, setIsHydrated] = useState(false);
  const { isAuthenticated, setShowLoginDialog } = useAuthStore();
  const router = useRouter();

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

  return <MarketplacePage />;
}
