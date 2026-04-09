'use client';

import { Users, BookOpen, Cpu, ScrollText, Sliders, TrendingUp } from 'lucide-react';
import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { cn } from '@/lib/utils';

const adminNavItems = [
  { icon: TrendingUp, label: '总览', href: '/admin/overview' },
  { icon: Users, label: '用户管理', href: '/admin/users' },
  { icon: BookOpen, label: '订阅配置', href: '/admin/providers' },
  { icon: Cpu, label: '模型配置', href: '/admin/models' },
  { icon: ScrollText, label: '操作日志', href: '/admin/logs' },
  { icon: Sliders, label: '系统设置', href: '/admin/settings' },
];

export function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 bg-white border-r border-gray-200 flex flex-col h-full">
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
                      ? 'bg-indigo-50 text-indigo-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  )}
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
      <div className="p-4 border-t border-gray-200">
        <p className="text-xs text-gray-400 text-center">© 2026 SharinMod</p>
      </div>
    </aside>
  );
}
