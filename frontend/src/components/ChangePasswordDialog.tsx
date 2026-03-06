'use client';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useAuthStore } from '@/lib/store';
import { ChangePasswordDialogContent } from './ChangePasswordDialogContent';
import { useTranslations } from 'next-intl';

export function ChangePasswordDialog() {
  const showChangePasswordDialog = useAuthStore((state) => state.showChangePasswordDialog);
  const setShowChangePasswordDialog = useAuthStore((state) => state.setShowChangePasswordDialog);
  const t = useTranslations('password');

  const handleOpenChange = (open: boolean) => {
    // 只允许打开弹框，不允许通过点击外部或 ESC 关闭
    // 必须通过修改密码成功来关闭
    if (open && !showChangePasswordDialog) {
      setShowChangePasswordDialog(true);
    }
  };

  return (
    <Dialog open={showChangePasswordDialog} onOpenChange={handleOpenChange}>
      <DialogContent
        className="sm:max-w-[425px]"
        onPointerDownOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>{t('changePassword')}</DialogTitle>
          <DialogDescription>
            {t('forceChangeDescription')}
          </DialogDescription>
        </DialogHeader>
        <ChangePasswordDialogContent onSuccess={() => setShowChangePasswordDialog(false)} />
      </DialogContent>
    </Dialog>
  );
}