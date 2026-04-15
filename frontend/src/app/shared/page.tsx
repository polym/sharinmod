'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import { MySharedPage } from '@/components/MySharedPage';

export default function SharedPage() {
  const [isHydrated, setIsHydrated] = useState(false);
  const { isAuthenticated, setShowLoginDialog, showResetPasswordDialog } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (!isHydrated) return;

    // Don't show login dialog if reset password dialog is open
    if (!isAuthenticated && !showResetPasswordDialog) {
      setShowLoginDialog(true);
    }
  }, [isAuthenticated, setShowLoginDialog, showResetPasswordDialog, isHydrated]);

  if (!isHydrated || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#121212] flex items-center justify-center">
        <div className="text-[#b3b3b3]">加载中...</div>
      </div>
    );
  }

  return <MySharedPage />;
}