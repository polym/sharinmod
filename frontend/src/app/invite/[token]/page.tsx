'use client';

import { useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { Loader2 } from 'lucide-react';
import { useAuthStore } from '@/lib/store';

export default function InvitePage() {
  const params = useParams<{ token: string }>();
  const token = params.token;
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const setShowLoginDialog = useAuthStore((state) => state.setShowLoginDialog);
  const setShowInviteDialog = useAuthStore((state) => state.setShowInviteDialog);
  const setRedirectAfterLogin = useAuthStore((state) => state.setRedirectAfterLogin);

  const setupInviteFlow = useCallback(() => {
    if (!token) return;

    if (isAuthenticated) {
      // 已登录用户：直接触发邀请弹窗
      setShowInviteDialog(true);
    } else {
      // 未登录用户：设置 redirectAfterLogin 并显示登录弹窗
      setRedirectAfterLogin(`/invite/${token}`);
      setShowLoginDialog(true);
    }
  }, [token, isAuthenticated, setShowInviteDialog, setShowLoginDialog, setRedirectAfterLogin]);

  useEffect(() => {
    setupInviteFlow();
  }, [setupInviteFlow]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-indigo-50 flex items-center justify-center">
      <div className="flex items-center gap-2 text-indigo-600">
        <Loader2 className="w-5 h-5 animate-spin" />
        <span>加载中...</span>
      </div>
    </div>
  );
}