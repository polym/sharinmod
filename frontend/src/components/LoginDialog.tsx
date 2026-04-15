'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { useAuthStore } from '@/lib/store';
import { LoginDialogContent } from './LoginDialogContent';
import { RegisterDialogContent } from './RegisterDialogContent';
import { useTranslations } from 'next-intl';

export function LoginDialog() {
  const showLoginDialog = useAuthStore((state) => state.showLoginDialog);
  const setShowLoginDialog = useAuthStore((state) => state.setShowLoginDialog);
  const t = useTranslations('loginDialog');
  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login');

  const handleOpenChange = (open: boolean) => {
    // Only allow opening; closing must happen via login success or cancel button
    if (open && !showLoginDialog) {
      setShowLoginDialog(true);
    }
  };

  const dialogTitle = activeTab === 'login' ? t('title') : t('registerTitle');

  return (
    <Dialog open={showLoginDialog} onOpenChange={handleOpenChange}>
      <DialogContent
        className="sm:max-w-[425px]"
        onPointerDownOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>{dialogTitle}</DialogTitle>
        </DialogHeader>
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'login' | 'register')}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="login">{t('loginTab')}</TabsTrigger>
            <TabsTrigger value="register">{t('registerTab')}</TabsTrigger>
          </TabsList>
          <TabsContent value="login" className="mt-4">
            <LoginDialogContent onSuccess={() => setShowLoginDialog(false)} />
          </TabsContent>
          <TabsContent value="register" className="mt-4">
            <RegisterDialogContent onSwitchToLogin={() => setActiveTab('login')} />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}

