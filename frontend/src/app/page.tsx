'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslations } from 'next-intl';

export default function HomePage() {
  const router = useRouter();
  const t = useTranslations('common');

  useEffect(() => {
    router.push('/marketplace');
  }, [router]);

  return (
    <div className="min-h-screen bg-[#121212] flex items-center justify-center">
      <div className="text-[#b3b3b3]">{t('loading')}</div>
    </div>
  );
}
