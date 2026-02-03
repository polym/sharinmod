'use client';

import { Card, CardContent } from '@/components/ui/card';

interface UsageStatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
}

export function UsageStatsCard({ title, value, subtitle }: UsageStatsCardProps) {
  return (
    <Card className="border-purple-100">
      <CardContent className="p-6">
        <div className="flex flex-col space-y-1">
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-400">{subtitle}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
