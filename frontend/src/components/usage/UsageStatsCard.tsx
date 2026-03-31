'use client';

import { Card, CardContent } from '@/components/ui/card';

interface UsageStatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
}

export function UsageStatsCard({ title, value, subtitle }: UsageStatsCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex flex-col space-y-2">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 tracking-tight">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 font-medium">{subtitle}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
