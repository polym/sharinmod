'use client';

import { Users, BookOpen, Cpu, ScrollText, Sliders, TrendingUp } from 'lucide-react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { cn } from '@/lib/utils';
import { useTranslations } from 'next-intl';

export function AdminSidebar() {
  const pathname = usePathname();
  const t = useTranslations('adminSidebar');

  const adminNavItems = [
    { icon: TrendingUp, label: t('overview'), href: '/admin/overview' },
    { icon: Users, label: t('users'), href: '/admin/users' },
    { icon: BookOpen, label: t('providers'), href: '/admin/providers' },
    { icon: Cpu, label: t('models'), href: '/admin/models' },
    { icon: ScrollText, label: t('logs'), href: '/admin/logs' },
    { icon: Sliders, label: t('settings'), href: '/admin/settings' },
  ];

  return (
    <aside className="w-56 bg-white/60 backdrop-blur-sm flex flex-col h-full">
      {/* Navigation */}
      <nav className="flex-1 px-3 py-4">
        <ul className="space-y-0.5">
          {adminNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    'w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-indigo-600 text-white shadow-md'
                      : 'text-gray-600 hover:bg-indigo-50/80 hover:text-indigo-700'
                  )}
                  style={isActive ? {
                    boxShadow: "0 2px 8px rgba(79, 70, 229, 0.15)"
                  } : {}}
                >
                  <Icon className="w-4 h-4 flex-shrink-0" />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4">
        <p className="text-xs text-gray-400 text-center">© 2026 SharinMod</p>
      </div>
    </aside>
  );
}
