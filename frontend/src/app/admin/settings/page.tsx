'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AdminSettings } from '@/components/admin-settings';
import { useAuthStore } from '@/lib/store';

export default function AdminSettingsPage() {
  const router = useRouter();
  const { user: currentUser, isAuthenticated, setShowLoginDialog } = useAuthStore();
  const [canAccess, setCanAccess] = useState(false);

  useEffect(() => {
    // 检查用户是否已登录
    if (!isAuthenticated) {
      setShowLoginDialog(true);
      return;
    }

    // 检查用户是否为管理员
    if (currentUser?.is_admin) {
      setCanAccess(true);
    } else {
      // 非管理员用户重定向到首页
      router.push('/marketplace');
    }
  }, [currentUser, isAuthenticated, router, setShowLoginDialog]);

  if (!canAccess) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-[#b3b3b3]">Access denied</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-8">
      <AdminSettings />
    </div>
  );
}
