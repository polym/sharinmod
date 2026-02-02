'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { UnifiedAPIKeys } from '@/components/unified-tokens';

export default function ApiKeysPage() {
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
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-8">
      <UnifiedAPIKeys />
    </div>
  );
}
