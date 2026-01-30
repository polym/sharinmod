'use client';

import { APIKeyDiscovery } from '@/components/token-discovery';

export function MarketplacePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">广场</h1>
        <p className="text-gray-500 mt-1">发现社区共享的 API Keys</p>
      </div>

      <APIKeyDiscovery />
    </div>
  );
}
