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
      className="w-60 bg-[#121212] flex flex-col h-full border-r border-[#282828]"
    >
      {/* Logo */}
      <div className="h-16 flex items-center px-6">
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-full flex items-center justify-center"
            style={{ backgroundColor: '#1ed760' }}
          >
            <span className="text-black font-bold text-xs">SM</span>
          </div>
          <span className="text-xl font-bold text-white tracking-tight">SharinMod</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4">
        <ul className="space-y-1">
          {visibleMenuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;
            return (
              <li key={item.id}>
                <button
                  onClick={() => onPageChange(item.id)}
                  className={cn(
                    'w-full flex items-center gap-3 px-4 py-3 rounded-full text-sm transition-all duration-200 cursor-pointer',
                    isActive
                      ? 'bg-[#1f1f1f] text-white font-bold'
                      : 'text-[#b3b3b3] hover:text-white hover:bg-[#1f1f1f] font-normal'
                  )}
                >
                  <Icon className={cn('w-5 h-5', isActive && 'text-[#1ed760]')} />
                  {t(item.labelKey)}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4">
        <div className="text-xs text-[#535353] text-center">
          © 2026 SharinMod
        </div>
      </div>
    </aside>
  );
}
