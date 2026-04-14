'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { User, LogOut, Zap, Lock, Globe } from 'lucide-react';
import { UserAvatar } from '@/components/UserAvatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAuthStore, useLocaleStore } from '@/lib/store';
import { cn } from '@/lib/utils';
import { authAPI } from '@/lib/services';
import { useIntervalOnVisible } from '@/hooks/useIntervalOnVisible';
import { useTranslations } from 'next-intl';

export function AdminHeader() {
  const { user, logout, updateUser, isAuthenticated, setShowProfileDialog, setShowChangePasswordDialog } = useAuthStore();
  const { locale, setLocale } = useLocaleStore();
  const router = useRouter();
  const t = useTranslations('adminHeader');
  const tTopbar = useTranslations('topbar');
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

  const toggleLocale = () => {
    setLocale(locale === 'zh-CN' ? 'en' : 'zh-CN');
  };

  return (
    <header className="bg-[#121212] border-b border-[#282828] px-8 py-4">
      <div className="flex items-center justify-between gap-8">
        {/* Left - Logo + Admin badge */}
        <div className="flex items-center gap-3">
          <Link href="/marketplace" className="flex items-center gap-2 hover:opacity-80 transition-opacity" aria-label={tLayout('backToApp')}>
            <div className="w-7 h-7 rounded-full flex items-center justify-center text-black font-bold text-xs" style={{ backgroundColor: '#1ed760' }}>
              SM
            </div>
            <span className="font-bold text-white text-sm">SharinMod</span>
          </Link>
          <span className="text-[#535353] text-sm">/</span>
          <span className="text-sm font-bold text-[#1ed760]">{tLayout('adminConsole')}</span>
        </div>

        {/* Right - Token balance + user menu */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 rounded-full bg-[#1f1f1f] px-4 py-1.5 border border-[#4d4d4d]">
            <Zap className="h-3.5 w-3.5 text-[#1ed760]" />
            <span className={cn(
              "text-sm font-bold",
              (user?.token_balance ?? 0) > 0 ? "text-white" : "text-[#ffa42b]"
            )}>
              {user?.token_balance ?? 0}
            </span>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className="focus:outline-none focus:ring-2 focus:ring-[#1ed760] focus:ring-offset-2 focus:ring-offset-[#121212] rounded-full cursor-pointer hover:opacity-80 transition-opacity"
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
            <DropdownMenuContent align="end" className="w-48 bg-[#282828] border-[#4d4d4d] text-white">
              <DropdownMenuItem
                className="cursor-pointer text-[#b3b3b3] hover:text-white focus:text-white focus:bg-[#3e3e3e]"
                onClick={() => setShowProfileDialog(true)}
              >
                <User className="mr-2 h-4 w-4" />
                {tTopbar('profile')}
              </DropdownMenuItem>
              <DropdownMenuItem
                className="cursor-pointer text-[#b3b3b3] hover:text-white focus:text-white focus:bg-[#3e3e3e]"
                onClick={() => setShowChangePasswordDialog(true)}
              >
                <Lock className="mr-2 h-4 w-4" />
                {tTopbar('changePassword')}
              </DropdownMenuItem>
              <DropdownMenuItem
                className="cursor-pointer text-[#b3b3b3] hover:text-white focus:text-white focus:bg-[#3e3e3e]"
                onClick={toggleLocale}
              >
                <Globe className="mr-2 h-4 w-4" />
                {locale === 'zh-CN' ? 'English' : '中文'}
              </DropdownMenuItem>
              <DropdownMenuSeparator className="bg-[#4d4d4d]" />
              <DropdownMenuItem
                className="cursor-pointer text-[#f3727f] focus:text-[#f3727f] focus:bg-[#3e3e3e]"
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
