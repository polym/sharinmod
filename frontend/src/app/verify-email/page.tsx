'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { useTranslations } from 'next-intl';

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const t = useTranslations('verifyEmail');

  const status = searchParams.get('status');
  const message = searchParams.get('message');

  if (status === 'success') {
    return (
      <div className="text-center space-y-4">
        <div className="text-5xl">✅</div>
        <h1 className="text-2xl font-bold">{t('successTitle')}</h1>
        <p className="text-muted-foreground">{t('successDescription')}</p>
        <Button asChild>
          <Link href="/">{t('goToLogin')}</Link>
        </Button>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="text-center space-y-4">
        <div className="text-5xl">❌</div>
        <h1 className="text-2xl font-bold">{t('errorTitle')}</h1>
        {message && (
          <p className="text-muted-foreground">{decodeURIComponent(message)}</p>
        )}
        <Button asChild variant="outline">
          <Link href="/">{t('backToHome')}</Link>
        </Button>
      </div>
    );
  }

  // No status param — user navigated here directly
  return (
    <div className="text-center space-y-4">
      <div className="text-5xl">⏳</div>
      <p className="text-muted-foreground">正在处理中...</p>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="max-w-md w-full rounded-2xl border bg-card p-8 shadow-sm">
        <Suspense fallback={<div className="text-center text-muted-foreground">加载中...</div>}>
          <VerifyEmailContent />
        </Suspense>
      </div>
    </div>
  );
}
