'use client';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useAuthStore } from '@/lib/store';
import { organizationAPI } from '@/lib/services';
import { Building2, Mail, CheckCircle2, XCircle, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useRouter } from 'next/navigation';
import { useState, useEffect, useCallback } from 'react';

interface InviteInfo {
  organization_name: string;
  organization_slug: string;
  expires_at: string;
  is_valid: boolean;
  inviter_email?: string;
}

export function InviteDialog() {
  const showInviteDialog = useAuthStore((state) => state.showInviteDialog);
  const setShowInviteDialog = useAuthStore((state) => state.setShowInviteDialog);
  const setMyOrganizations = useAuthStore((state) => state.setMyOrganizations);

  const router = useRouter();
  const [inviteInfo, setInviteInfo] = useState<InviteInfo | null>(null);
  const [accepting, setAccepting] = useState(false);
  const [acceptSuccess, setAcceptSuccess] = useState(false);
  const [acceptError, setAcceptError] = useState<string | null>(null);
  const [loadingError, setLoadingError] = useState<string | null>(null);

  const handleOpenChange = (open: boolean) => {
    // 不允许通过外部点击或 ESC 关闭
    if (open && !showInviteDialog) {
      setShowInviteDialog(true);
    }
  };

  const handleAccept = async () => {
    if (!inviteInfo || !inviteInfo.is_valid) return;

    setAccepting(true);
    setAcceptError(null);
    try {
      await organizationAPI.acceptInvite(getInviteToken());
      setAcceptSuccess(true);
      // Refresh org store so OrganizationSwitcher reflects the newly joined org
      try {
        const orgsResponse = await organizationAPI.getMyOrganizations();
        setMyOrganizations(orgsResponse.data);
      } catch {
        // Non-fatal: store will be refreshed on next navigation
      }
    } catch (error: any) {
      setAcceptError(error.response?.data?.detail || '接受邀请失败，请稍后重试');
    } finally {
      setAccepting(false);
    }
  };

  const handleClose = () => {
    // Reset all states when closing
    setShowInviteDialog(false);
    setInviteInfo(null);
    setAcceptSuccess(false);
    setAcceptError(null);
    setLoadingError(null);
    router.push('/marketplace');
  };

  const getInviteToken = useCallback((): string => {
    if (typeof window === 'undefined') return '';
    const path = window.location.pathname;
    const match = path.match(/\/invite\/([^/]+)/);
    return match ? match[1] : '';
  }, []);

  // Load invite info when dialog opens
  useEffect(() => {
    if (showInviteDialog) {
      const token = getInviteToken();
      // Reset states when dialog opens
      setInviteInfo(null);
      setAcceptSuccess(false);
      setAcceptError(null);
      setLoadingError(null);

      if (token) {
        organizationAPI.getInviteInfo(token)
          .then(response => setInviteInfo(response.data))
          .catch(error => {
            if (error.response?.status === 404) {
              setLoadingError('邀请链接不存在或已失效');
            } else {
              setLoadingError('加载邀请信息失败，请稍后重试');
            }
          });
      } else {
        setLoadingError('无效的邀请链接');
      }
    }
  }, [showInviteDialog, getInviteToken]);

  // Show loading state or error
  if (loadingError) {
    return (
      <Dialog open={showInviteDialog} onOpenChange={handleOpenChange}>
        <DialogContent
          className="sm:max-w-[425px]"
          onPointerDownOutside={(e) => e.preventDefault()}
          onEscapeKeyDown={(e) => e.preventDefault()}
        >
          <DialogHeader className="text-center">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-2">
              <AlertCircle className="w-6 h-6 text-red-600" />
            </div>
            <DialogTitle className="text-red-600">邀请链接无效</DialogTitle>
            <DialogDescription>{loadingError}</DialogDescription>
          </DialogHeader>
          <div className="flex justify-center">
            <Button onClick={handleClose}>关闭</Button>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  if (!inviteInfo && showInviteDialog) {
    return (
      <Dialog open={showInviteDialog} onOpenChange={handleOpenChange}>
        <DialogContent
          className="sm:max-w-[425px]"
          onPointerDownOutside={(e) => e.preventDefault()}
          onEscapeKeyDown={(e) => e.preventDefault()}
        >
          <DialogHeader className="text-center">
            <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-2">
              <Loader2 className="w-6 h-6 text-indigo-600 animate-spin" />
            </div>
            <DialogTitle>加载邀请信息中...</DialogTitle>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    );
  }

  if (!inviteInfo) {
    return null;
  }

  return (
    <Dialog open={showInviteDialog} onOpenChange={handleOpenChange}>
      <DialogContent
        className="sm:max-w-[425px]"
        onPointerDownOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        <DialogHeader className="text-center">
          <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-2">
            <Building2 className="w-6 h-6 text-indigo-600" />
          </div>
          <DialogTitle>您被邀请加入私服：{inviteInfo.organization_name}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {inviteInfo.inviter_email && (
            <div className="flex items-center gap-2 text-sm text-indigo-600 bg-indigo-50 rounded-lg p-3 border border-indigo-100">
              <Mail className="w-4 h-4" />
              <span>邀请者：{inviteInfo.inviter_email}</span>
            </div>
          )}

          {!inviteInfo.is_valid && (
            <div className="flex items-center gap-2 text-sm text-amber-600 bg-amber-50 rounded-lg p-3 border border-amber-200">
              <XCircle className="w-4 h-4" />
              <span>邀请链接已过期或已被使用</span>
            </div>
          )}

          {acceptSuccess && (
            <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 rounded-lg p-3 border border-green-200">
              <CheckCircle2 className="w-4 h-4" />
              <span>加入成功！您现在可以在顶部切换到该私服。</span>
            </div>
          )}

          {acceptError && (
            <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 rounded-lg p-3 border border-red-200">
              <XCircle className="w-4 h-4" />
              <span>{acceptError}</span>
            </div>
          )}

          {inviteInfo.is_valid && !acceptSuccess ? (
            <>
              <Button
                className="w-full bg-indigo-600 hover:bg-indigo-700"
                onClick={handleAccept}
                disabled={accepting}
              >
                {accepting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    处理中...
                  </>
                ) : '接受邀请'}
              </Button>
              <Button variant="outline" className="w-full" onClick={handleClose}>
                暂不加入
              </Button>
            </>
          ) : (
            <Button className="w-full bg-indigo-600 hover:bg-indigo-700" onClick={handleClose}>
              前往首页
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}