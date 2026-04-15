'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/lib/store';

export default function ResetPasswordPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const setShowResetPasswordDialog = useAuthStore((state) => state.setShowResetPasswordDialog);

  const token = searchParams.get('token');

  useEffect(() => {
    if (token) {
      // Show reset password dialog with token
      setShowResetPasswordDialog(true, token);
    }
    // Always redirect to shared - the dialog will show there
    router.replace('/shared');
  }, [token, setShowResetPasswordDialog, router]);

  // Show loading while redirecting
  return (
    <div className="min-h-screen bg-[#121212] flex items-center justify-center">
      <div className="text-[#b3b3b3]">加载中...</div>
    </div>
  );
}
