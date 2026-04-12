'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Settings, LogOut, Zap } from 'lucide-react';
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
import { useTranslations } from 'next-intl';

export function AdminHeader() {
  const { user, logout, updateUser, isAuthenticated } = useAuthStore();
  const router = useRouter();
  const t = useTranslations('adminHeader');
  const tLayout = useTranslations('adminLayout');

  const handleLogout = () => {
    logout();
    router.push('/shared');
  };

  const refreshTokenBalance = async () => {
    const currentUser = useAuthStore.getState().user;
    if (!currentUser) return;
    try {
      const response = await authAPI.getProfile();
      updateUser(response.data);
    } catch {
      // Silently fail
    }
  };

  useIntervalOnVisible(refreshTokenBalance, isAuthenticated ? 20000 : null);

  return (
    <header
      className="bg-gradient-to-r from-white via-indigo-50/30 to-white border-b border-gray-200 px-8 py-4"
      style={{
        boxShadow: "0 4px 0 rgba(79, 70, 229, 0.08), 0 8px 16px rgba(79, 70, 229, 0.05)"
      }}
    >
      <div className="flex items-center justify-between gap-8">
        {/* Left - Logo + Admin badge */}
        <div className="flex items-center gap-3">
          <Link href="/marketplace" className="flex items-center gap-2 hover:opacity-90 transition-opacity" aria-label={tLayout('backToApp')}>
            <div
              className="w-7 h-7 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl flex items-center justify-center text-white font-bold text-xs border-2 border-indigo-300"
              style={{
                boxShadow: "0 3px 0 rgba(79, 70, 229, 0.25), 0 6px 12px rgba(79, 70, 229, 0.15)"
              }}
            >
              SM
            </div>
            <span className="font-semibold text-gray-900 text-sm">SharinMod</span>
          </Link>
          <span className="text-gray-300 text-sm">/</span>
          <div className="px-2.5 py-1 rounded-md bg-indigo-50 border border-indigo-200">
            <span className="text-xs font-medium text-indigo-700">{tLayout('adminConsole')}</span>
          </div>
        </div>

        {/* Right - Token balance + user menu */}
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            className="bg-gradient-to-r from-indigo-100 to-indigo-50 gap-1.5 h-8 px-3 rounded-xl border-2 border-indigo-200 shadow-sm hover:shadow-md"
            style={{
              boxShadow: "0 2px 0 rgba(79, 70, 229, 0.15), 0 4px 8px rgba(79, 70, 229, 0.1)"
            }}
          >
            <Zap className="h-3.5 w-3.5 text-indigo-600" />
            <span className={cn(
              "text-sm font-medium",
              (user?.token_balance ?? 0) > 0 ? "text-indigo-600" : "text-orange-500"
            )}>
              {user?.token_balance ?? 0}
            </span>
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className="focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded-full p-1 bg-gradient-to-br from-indigo-100 to-indigo-50 border-2 border-indigo-200 hover:shadow-md transition-all cursor-pointer"
                style={{
                  boxShadow: "0 2px 0 rgba(79, 70, 229, 0.15), 0 4px 8px rgba(79, 70, 229, 0.1)"
                }}
                aria-label={tLayout('userMenu')}
              >
                <UserAvatar
                  email={user?.email}
                  name={user?.name}
                  avatar_url={user?.avatar_url}
                  className="h-8 w-8"
                />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuItem
                className="cursor-pointer"
                onClick={() => router.push('/settings')}
              >
                <Settings className="mr-2 h-4 w-4" />
                {t('settings')}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="cursor-pointer text-red-600 focus:text-red-600"
                onClick={handleLogout}
              >
                <LogOut className="mr-2 h-4 w-4" />
                {t('logout')}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
