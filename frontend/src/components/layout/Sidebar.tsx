'use client';

import { Store, Key, BarChart3, Share } from 'lucide-react';
import { cn } from '@/lib/utils';

export type PageType = 'marketplace' | 'my-shared' | 'api-keys' | 'usage' | 'settings' | 'admin-users';

interface SidebarProps {
  currentPage: PageType;
  onPageChange: (page: PageType) => void;
}

const menuItems = [
  { id: 'marketplace' as PageType, label: '广场', icon: Store },
  { id: 'my-shared' as PageType, label: '我的共享', icon: Share },
  { id: 'api-keys' as PageType, label: 'API Keys', icon: Key },
  { id: 'usage' as PageType, label: '使用情况', icon: BarChart3 },
];

export function Sidebar({ currentPage, onPageChange }: SidebarProps) {
  return (
    <aside className="w-60 bg-brand-50 border-r border-gray-200 flex flex-col h-full">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">SM</span>
          </div>
          <span className="text-xl font-bold text-gray-900">SharinMod</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4">
        <ul className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <li key={item.id}>
                <button
                  onClick={() => onPageChange(item.id)}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-brand-500 text-white'
                      : 'text-gray-700 hover:bg-white hover:text-gray-900'
                  )}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="text-xs text-gray-500 text-center">
          © 2026 SharinMod
        </div>
      </div>
    </aside>
  );
}
