'use client';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useAuthStore } from '@/lib/store';
import { LoginDialogContent } from './LoginDialogContent';
import { useTranslations } from 'next-intl';

export function LoginDialog() {
  const showLoginDialog = useAuthStore((state) => state.showLoginDialog);
  const setShowLoginDialog = useAuthStore((state) => state.setShowLoginDialog);
  const t = useTranslations('loginDialog');

  const handleOpenChange = (open: boolean) => {
    // 只允许打开弹框，不允许通过点击外部或 ESC 关闭
    // 必须通过登录成功或取消按钮来关闭
    if (open && !showLoginDialog) {
      setShowLoginDialog(true);
    }
  };

  return (
    <Dialog open={showLoginDialog} onOpenChange={handleOpenChange}>
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
        <LoginDialogContent onSuccess={() => setShowLoginDialog(false)} />
      </DialogContent>
    </Dialog>
  );
}
