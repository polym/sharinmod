'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { MySharedPage } from '@/components/MySharedPage';

export default function SharedPage() {
  const [isHydrated, setIsHydrated] = useState(false);
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (!isHydrated) return;
    
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
  }, [isAuthenticated, router, isHydrated]);

  if (!isHydrated || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  return <MySharedPage />;
}
