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
    <aside
      className="w-60 bg-gradient-to-br from-indigo-50 via-white to-indigo-50 border-r-2 border-indigo-100 flex flex-col h-full"
      style={{
        boxShadow: "4px 0 16px rgba(79, 70, 229, 0.1)"
      }}
    >
      {/* Logo - Claymorphism Style */}
      <div className="h-16 flex items-center px-6 border-b-2 border-indigo-100">
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl flex items-center justify-center border-2 border-indigo-300"
            style={{
              boxShadow: "0 3px 0 rgba(79, 70, 229, 0.25), 0 6px 12px rgba(79, 70, 229, 0.15)"
            }}
          >
            <span className="text-white font-bold text-sm">SM</span>
          </div>
          <span className="text-xl font-bold text-gray-900">SharinMod</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <li key={item.id}>
                <button
                  onClick={() => onPageChange(item.id)}
                  className={cn(
                    'w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-medium transition-all border-2 relative',
                    isActive
                      ? 'bg-gradient-to-br from-indigo-500 to-indigo-600 text-white border-indigo-300 shadow-lg'
                      : 'text-gray-700 hover:bg-white hover:text-indigo-600 hover:border-indigo-200 border-transparent hover:shadow-md'
                  )}
                  style={isActive ? {
                    boxShadow: "0 4px 0 rgba(79, 70, 229, 0.3), 0 8px 16px rgba(79, 70, 229, 0.2)"
                  } : {}}
                >
                  <Icon className="w-5 h-5" />
                  {item.label}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer - Claymorphism Style */}
      <div className="p-4 border-t-2 border-indigo-100">
        <div
          className="text-xs text-indigo-400 text-center bg-gradient-to-r from-indigo-50 to-white rounded-xl p-2 border border-indigo-100"
          style={{
            boxShadow: "inset 0 1px 3px rgba(79, 70, 229, 0.1)"
          }}
        >
          © 2026 SharinMod
        </div>
      </div>
    </aside>
  );
}
