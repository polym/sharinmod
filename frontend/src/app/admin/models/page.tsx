'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AdminModelConfig } from '@/components/admin-model-config';
import { useAuthStore } from '@/lib/store';

export default function AdminModelsPage() {
  const router = useRouter();
  const { user: currentUser, isAuthenticated, setShowLoginDialog } = useAuthStore();
  const [canAccess, setCanAccess] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      setShowLoginDialog(true);
      return;
    }

    if (currentUser?.is_admin) {
      setCanAccess(true);
    } else {
      router.push('/marketplace');
    }
  }, [currentUser, isAuthenticated, router, setShowLoginDialog]);

  if (!canAccess) {
    return (
      <div className="min-h-screen bg-[#121212] flex items-center justify-center">
        <div className="text-[#b3b3b3]">Access denied</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-8 space-y-6">
      <AdminModelConfig />
    </div>
  );
}
