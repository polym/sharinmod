'use client';

import { useRouter } from 'next/navigation';
import { Settings, Key, LogOut, Zap, Shield } from 'lucide-react';
import { UserAvatar } from '@/components/UserAvatar';
import { Button } from '@/components/ui/button';
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
    <header
      className="h-16 bg-gradient-to-r from-white via-indigo-50/30 to-white border-b-2 border-indigo-100 flex items-center justify-between px-6"
      style={{
        boxShadow: "0 4px 0 rgba(79, 70, 229, 0.08), 0 8px 16px rgba(79, 70, 229, 0.05)"
      }}
    >
      {/* Left side - can add page title or breadcrumb */}
      <div />

      {/* Right side - User menu */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          className="bg-gradient-to-r from-indigo-100 to-indigo-50 gap-1.5 rounded-xl border-2 border-indigo-200 shadow-sm hover:shadow-md"
          style={{
            boxShadow: "0 2px 0 rgba(79, 70, 229, 0.15), 0 4px 8px rgba(79, 70, 229, 0.1)"
          }}
        >
          <Zap className="h-4 w-4 text-indigo-600" />
          <span className={cn(
            "text-sm font-medium",
            (user?.token_balance ?? 0) > 0 ? "text-indigo-600" : "text-orange-500"
          )}>
            {user?.token_balance ?? 0}
          </span>
        </Button>
        <span className="text-sm text-gray-600 hidden sm:block">
          {user?.email}
        </span>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded-full p-1 bg-gradient-to-br from-indigo-100 to-indigo-50 border-2 border-indigo-200 hover:shadow-md transition-all"
              style={{
                boxShadow: "0 2px 0 rgba(79, 70, 229, 0.15), 0 4px 8px rgba(79, 70, 229, 0.1)"
              }}
            >
              <UserAvatar
                email={user?.email}
                name={user?.name}
                avatar_url={user?.avatar_url}
                className="h-10 w-10 cursor-pointer"
              />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuItem
              className="cursor-pointer"
              onClick={() => onPageChange('settings')}
            >
              <Settings className="mr-2 h-4 w-4" />
              设置
            </DropdownMenuItem>
            <DropdownMenuItem
              className="cursor-pointer"
              onClick={() => onPageChange('api-keys')}
            >
              <Key className="mr-2 h-4 w-4" />
              API Keys
            </DropdownMenuItem>
            {user?.is_admin && (
              <>
                <DropdownMenuItem
                  className="cursor-pointer"
                  onClick={() => onPageChange('admin-users')}
                >
                  <Shield className="mr-2 h-4 w-4" />
                  Admin 看板
                </DropdownMenuItem>
                <DropdownMenuSeparator />
              </>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="cursor-pointer text-red-600 focus:text-red-600"
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
