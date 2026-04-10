'use client';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useAuthStore } from '@/lib/store';
import { useTranslations } from 'next-intl';
import { ChangePasswordDialogContentFromMenu } from './ChangePasswordDialogContentFromMenu';

export function ChangePasswordDialogFromMenu() {
  const showChangePasswordDialog = useAuthStore((state) => state.showChangePasswordDialog);
  const setShowChangePasswordDialog = useAuthStore((state) => state.setShowChangePasswordDialog);
  const t = useTranslations('password');

  return (
    <Dialog open={showChangePasswordDialog} onOpenChange={setShowChangePasswordDialog}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{t('changePassword')}</DialogTitle>
          <DialogDescription>
            {t('description')}
          </DialogDescription>
        </DialogHeader>
        <ChangePasswordDialogContentFromMenu onSuccess={() => setShowChangePasswordDialog(false)} />
      </DialogContent>
    </Dialog>
  );
}
