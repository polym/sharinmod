'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { AdminSidebar } from '@/components/layout/AdminSidebar';
import { AdminHeader } from '@/components/layout/AdminHeader';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, isAuthenticated, setShowLoginDialog } = useAuthStore();
  const [canAccess, setCanAccess] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      setShowLoginDialog(true);
      return;
    }
    if (user?.is_admin) {
      setCanAccess(true);
    } else {
      router.push('/marketplace');
    }
  }, [user, isAuthenticated, router, setShowLoginDialog]);

  if (!canAccess) {
    return (
      <div className="flex h-screen items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-indigo-50">
        <div className="text-indigo-400">加载中...</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gradient-to-br from-indigo-50 via-white to-indigo-50 overflow-hidden">
      {/* Admin Header - fixed at top */}
      <div className="fixed top-0 left-0 right-0 z-50 w-full">
        <AdminHeader />
      </div>

      {/* Admin Sidebar - fixed below header */}
      <div className="fixed top-16 left-0 h-[calc(100vh-4rem)] z-40 w-56">
        <AdminSidebar />
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0 pt-16 pl-56">
        <main className="flex-1 overflow-auto p-4 md:p-6 bg-gradient-to-br from-indigo-50/50 via-transparent to-indigo-50/30">
          {children}
        </main>
      </div>
    </div>
  );
}
