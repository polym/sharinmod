'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useAuthStore } from '@/lib/store';
import { ResetPasswordDialogContent } from './ResetPasswordDialogContent';
import { useTranslations } from 'next-intl';

export function ResetPasswordDialog() {
  const showResetPasswordDialog = useAuthStore((state) => state.showResetPasswordDialog);
  const setShowResetPasswordDialog = useAuthStore((state) => state.setShowResetPasswordDialog);
  const resetPasswordToken = useAuthStore((state) => state.resetPasswordToken);
  const t = useTranslations('passwordReset');
  const router = useRouter();

  const handleOpenChange = (open: boolean) => {
    // 只允许通过关闭按钮关闭，不允许通过点击外部或 ESC 关闭
    if (!open && showResetPasswordDialog) {
      setShowResetPasswordDialog(false);
      // Redirect to shared when dialog closes
      router.push('/shared');
    }
  };

  const handleSuccess = () => {
    setShowResetPasswordDialog(false);
    // Redirect after successful password reset
    router.push('/shared');
  };

  const handleCancel = () => {
    setShowResetPasswordDialog(false);
    // Redirect to shared when cancelled
    router.push('/shared');
  };

  return (
    <Dialog open={showResetPasswordDialog} onOpenChange={handleOpenChange}>
      <DialogContent
        className="sm:max-w-[425px]"
        onPointerDownOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>{t('title')}</DialogTitle>
          <DialogDescription>
            {t('description')}
          </DialogDescription>
        </DialogHeader>
        <ResetPasswordDialogContent
          token={resetPasswordToken}
          onSuccess={handleSuccess}
          onCancel={handleCancel}
        />
      </DialogContent>
    </Dialog>
  );
}