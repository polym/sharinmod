'use client';

import { Card, CardContent } from '@/components/ui/card';

interface UsageStatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
}

export function UsageStatsCard({ title, value, subtitle }: UsageStatsCardProps) {
  return (
    <Card className="clay-card border-[3px] border-indigo-100 bg-gradient-to-br from-white to-indigo-50/30">
      <CardContent className="p-6">
        <div className="flex flex-col space-y-2">
          <p className="text-sm font-semibold text-indigo-700">{title}</p>
          <p className="text-3xl font-bold text-indigo-900 tracking-tight font-heading">{value}</p>
          {subtitle && (
            <p className="text-xs text-indigo-500 font-medium">{subtitle}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
