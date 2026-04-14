'use client';

import { useRouter } from 'next/navigation';
import { Settings, Key, LogOut, Zap, Shield } from 'lucide-react';
import { UserAvatar } from '@/components/UserAvatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAuthStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import { authAPI } from '@/lib/services';
import { useIntervalOnVisible } from '@/hooks/useIntervalOnVisible';
import { OrganizationSwitcher } from '@/components/OrganizationSwitcher';
import type { PageType } from './Sidebar';

interface TopBarProps {
  onPageChange: (page: PageType) => void;
}

export function TopBar({ onPageChange }: TopBarProps) {
  const { user, logout, setShowLoginDialog, updateUser, isAuthenticated } = useAuthStore();
  const router = useRouter();

  console.log('[TopBar] Render, isAuthenticated:', isAuthenticated, 'user:', user ? `${user.email} (balance: ${user.token_balance})` : 'null');

  const handleLogout = () => {
    logout();
    router.push('/shared');
  };

  // Auto-refresh token balance every minute when page is visible
  const refreshTokenBalance = async () => {
    // Get fresh user state from store to avoid closure issues
    const currentUser = useAuthStore.getState().user;
    if (!currentUser) return; // Only refresh if user is logged in
    try {
      console.log('[TopBar] Refreshing token balance...');
      const response = await authAPI.getProfile();
      console.log('[TopBar] Token balance updated:', response.data.token_balance);
      updateUser(response.data);
    } catch (error) {
      console.error('[TopBar] Failed to refresh token balance:', error);
      // Silently fail - axios interceptor will handle 401 errors
    }
  };

  useIntervalOnVisible(refreshTokenBalance, isAuthenticated ? 20000 : null);

  return (
    <header className="h-16 bg-[#121212] border-b border-[#282828] flex items-center justify-between px-6">
      {/* Left side - Organization switcher */}
      <OrganizationSwitcher />

      {/* Right side - User menu */}
      <div className="flex items-center gap-4">
        <button
          className="flex items-center gap-1.5 rounded-full bg-[#1f1f1f] px-4 py-2 text-sm font-bold cursor-default border border-[#4d4d4d] transition-colors hover:bg-[#282828]"
        >
          <Zap className="h-4 w-4 text-[#1ed760]" />
          <span className={cn(
            "text-sm font-bold",
            (user?.token_balance ?? 0) > 0 ? "text-white" : "text-[#ffa42b]"
          )}>
            {user?.token_balance ?? 0}
          </span>
        </button>
        <span className="text-sm text-[#b3b3b3] hidden sm:block">
          {user?.email}
        </span>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="focus:outline-none focus:ring-2 focus:ring-[#1ed760] focus:ring-offset-2 focus:ring-offset-[#121212] rounded-full cursor-pointer hover:opacity-80 transition-opacity"
            >
              <UserAvatar
                email={user?.email}
                name={user?.name}
                avatar_url={user?.avatar_url}
                className="h-9 w-9"
              />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48 bg-[#282828] border-[#4d4d4d] text-white">
            <DropdownMenuItem
              className="cursor-pointer text-[#b3b3b3] hover:text-white focus:text-white focus:bg-[#3e3e3e]"
              onClick={() => onPageChange('settings')}
            >
              <Settings className="mr-2 h-4 w-4" />
              设置
            </DropdownMenuItem>
            <DropdownMenuItem
              className="cursor-pointer text-[#b3b3b3] hover:text-white focus:text-white focus:bg-[#3e3e3e]"
              onClick={() => onPageChange('api-keys')}
            >
              <Key className="mr-2 h-4 w-4" />
              API Keys
            </DropdownMenuItem>
            {user?.is_admin && (
              <>
                <DropdownMenuItem
                  className="cursor-pointer text-[#b3b3b3] hover:text-white focus:text-white focus:bg-[#3e3e3e]"
                  onClick={() => onPageChange('admin-users')}
                >
                  <Shield className="mr-2 h-4 w-4" />
                  Admin 看板
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-[#4d4d4d]" />
              </>
            )}
            <DropdownMenuSeparator className="bg-[#4d4d4d]" />
            <DropdownMenuItem
              className="cursor-pointer text-[#f3727f] focus:text-[#f3727f] focus:bg-[#3e3e3e]"
              onClick={handleLogout}
            >
              <LogOut className="mr-2 h-4 w-4" />
              登出
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
