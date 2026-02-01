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

export function LoginDialog() {
  const showLoginDialog = useAuthStore((state) => state.showLoginDialog);
  const setShowLoginDialog = useAuthStore((state) => state.setShowLoginDialog);

  return (
    <Dialog open={showLoginDialog} onOpenChange={setShowLoginDialog}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>登录 SharinMod</DialogTitle>
          <DialogDescription>
            输入您的凭据来访问平台
          </DialogDescription>
        </DialogHeader>
        <LoginDialogContent onSuccess={() => setShowLoginDialog(false)} />
      </DialogContent>
    </Dialog>
  );
}
