'use client';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useAuthStore } from '@/lib/store';
import { RegisterDialogContent } from './RegisterDialogContent';

export function RegisterDialog() {
  const showRegisterDialog = useAuthStore((state) => state.showRegisterDialog);
  const setShowRegisterDialog = useAuthStore((state) => state.setShowRegisterDialog);

  const handleOpenChange = (open: boolean) => {
    // 只允许打开弹框，不允许通过点击外部或 ESC 关闭
    // 必须通过注册成功或切换到登录来关闭
    if (open && !showRegisterDialog) {
      setShowRegisterDialog(true);
    }
  };

  return (
    <Dialog open={showRegisterDialog} onOpenChange={handleOpenChange}>
      <DialogContent
        className="sm:max-w-[425px]"
        onPointerDownOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>注册 SharinMod</DialogTitle>
          <DialogDescription>
            创建您的账户来开始分享和使用 API tokens
          </DialogDescription>
        </DialogHeader>
        <RegisterDialogContent onSuccess={() => setShowRegisterDialog(false)} />
      </DialogContent>
    </Dialog>
  );
}
