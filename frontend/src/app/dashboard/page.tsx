'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { DashboardLayout, PageType } from '@/components/layout/DashboardLayout';
import { MarketplacePage } from '@/components/MarketplacePage';
import { MySharedPage } from '@/components/MySharedPage';
import { UnifiedAPIKeys } from '@/components/unified-tokens';
import { APIKeyUsage } from '@/components/token-usage';
import { ProfileSettings } from '@/components/profile-settings';

export default function DashboardPage() {
  const [currentPage, setCurrentPage] = useState<PageType>('marketplace');
  const [isHydrated, setIsHydrated] = useState(false);
  const { isAuthenticated } = useAuthStore();
  const router = useRouter();

  // Wait for Zustand hydration
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

  const renderContent = () => {
    switch (currentPage) {
      case 'marketplace':
        return <MarketplacePage />;
      case 'my-shared':
        return <MySharedPage />;
      case 'api-keys':
        return (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">API Keys</h1>
              <p className="text-gray-500 mt-1">管理您的统一 API Keys</p>
            </div>
            <UnifiedAPIKeys />
          </div>
        );
      case 'usage':
        return (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">使用情况</h1>
              <p className="text-gray-500 mt-1">查看 API Key 使用历史</p>
            </div>
            <APIKeyUsage />
          </div>
        );
      case 'settings':
        return (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">设置</h1>
              <p className="text-gray-500 mt-1">管理您的个人资料</p>
            </div>
            <ProfileSettings />
          </div>
        );
      default:
        return <MarketplacePage />;
    }
  };

  return (
    <DashboardLayout currentPage={currentPage} onPageChange={setCurrentPage}>
      {renderContent()}
    </DashboardLayout>
  );
}