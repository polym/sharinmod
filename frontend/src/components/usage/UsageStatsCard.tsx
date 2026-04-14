'use client';

import { Card, CardContent } from '@/components/ui/card';

interface UsageStatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
}

export function UsageStatsCard({ title, value, subtitle }: UsageStatsCardProps) {
  return (
    <Card className=" border border-[#282828] bg-[#181818]">
      <CardContent className="p-6">
        <div className="flex flex-col space-y-2">
          <p className="text-sm font-semibold text-[#b3b3b3]">{title}</p>
          <p className="text-3xl font-bold text-white tracking-tight font-heading">{value}</p>
          {subtitle && (
            <p className="text-xs text-[#b3b3b3] font-medium">{subtitle}</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
