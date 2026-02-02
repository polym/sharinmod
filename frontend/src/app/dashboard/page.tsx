'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';

export default function DashboardPage() {
  const [isHydrated, setIsHydrated] = useState(false);
  const { isAuthenticated, setShowLoginDialog } = useAuthStore();
  const router = useRouter();

  // Wait for Zustand hydration
  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (!isHydrated) return;
    
    if (!isAuthenticated) {
      setShowLoginDialog(true);
      return;
    }
    
    // 重定向到 marketplace
    router.push('/marketplace');
  }, [isAuthenticated, setShowLoginDialog, router, isHydrated]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-gray-500">加载中...</div>
    </div>
  );
}