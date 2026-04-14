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
    <aside className="w-56 bg-[#121212] flex flex-col h-full border-r border-[#282828]">
      {/* Navigation */}
      <nav className="flex-1 px-3 py-4">
        <ul className="space-y-1">
          {adminNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    'w-full flex items-center gap-2.5 px-3 py-2.5 rounded-full text-sm transition-colors duration-200',
                    isActive
                      ? 'bg-[#1f1f1f] text-white font-bold'
                      : 'text-[#b3b3b3] hover:text-white hover:bg-[#1f1f1f] font-normal'
                  )}
                >
                  <Icon className={cn('w-4 h-4 flex-shrink-0', isActive && 'text-[#1ed760]')} />
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4">
        <p className="text-xs text-[#535353] text-center">© 2026 SharinMod</p>
      </div>
    </aside>
  );
}
