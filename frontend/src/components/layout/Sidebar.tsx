'use client';

import { Store, Key, BarChart3, Share, Users } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/lib/store';
import { useTranslations } from 'next-intl';

export type PageType = 'overview' | 'marketplace' | 'my-shared' | 'api-keys' | 'usage' | 'settings' | 'admin-users' | 'my-team';

interface SidebarProps {
  currentPage: PageType;
  onPageChange: (page: PageType) => void;
}

export function Sidebar({ currentPage, onPageChange }: SidebarProps) {
  const t = useTranslations('sidebar');

  const menuItems = [
    { id: 'overview' as PageType, labelKey: 'overview', icon: BarChart3 },
    { id: 'marketplace' as PageType, labelKey: 'marketplace', icon: Store },
    { id: 'my-shared' as PageType, labelKey: 'myShared', icon: Share },
    { id: 'api-keys' as PageType, labelKey: 'apiKeys', icon: Key },
    { id: 'usage' as PageType, labelKey: 'usage', icon: BarChart3 },
    { id: 'my-team' as PageType, labelKey: 'myTeam', icon: Users },
  ];
  const { user, currentOrganization, myOrganizations } = useAuthStore();

  // Check if user is org owner
  const isOrgOwner = currentOrganization && myOrganizations?.owned.some(org => org.id === currentOrganization.id);

  // Determine menu items to show
  // - Public mode (no organization): show all menu items
  // - Private mode + owner: show all menu items
  // - Private mode + non-owner: hide "overview" and "my-team" menu items
  const showMenuItems = () => {
    if (!currentOrganization) {
      // Public mode
      return menuItems;
    } else if (isOrgOwner) {
      // Private mode + owner
      return menuItems;
    } else {
      // Private mode + non-owner - hide overview and my-team
      return menuItems.filter(item => item.id !== 'overview' && item.id !== 'my-team');
    }
  };

  const visibleMenuItems = showMenuItems();

  return (
    <aside
      className="w-60 bg-white/60 backdrop-blur-sm flex flex-col h-full"
      style={{
        boxShadow: "inset -1px 0 0 rgba(79, 70, 229, 0.06)"
      }}
    >
      {/* Logo - Claymorphism Style */}
      <div className="h-16 flex items-center px-6">
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
          {visibleMenuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <li key={item.id}>
                <button
                  onClick={() => onPageChange(item.id)}
                  className={cn(
                    'w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all',
                    isActive
                      ? 'bg-indigo-600 text-white shadow-lg'
                      : 'text-gray-600 hover:bg-indigo-50 hover:text-indigo-700'
                  )}
                  style={isActive ? {
                    boxShadow: "0 2px 8px rgba(79, 70, 229, 0.2), 0 8px 16px rgba(79, 70, 229, 0.12)"
                  } : {}}
                >
                  <Icon className="w-5 h-5" />
                  {t(item.labelKey)}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer - Claymorphism Style */}
      <div className="p-4">
        <div
          className="text-xs text-indigo-400 text-center bg-indigo-50/50 rounded-xl p-2"
        >
          © 2026 SharinMod
        </div>
      </div>
    </aside>
  );
}
