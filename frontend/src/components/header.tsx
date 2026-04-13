"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { User, LogOut, Zap, Shield, Lock, Globe } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore, useLocaleStore } from "@/lib/store";
import { authAPI } from "@/lib/services";
import { useIntervalOnVisible } from "@/hooks/useIntervalOnVisible";
import { UserAvatar } from "@/components/UserAvatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useTranslations } from "next-intl";

export function Header() {
  const t = useTranslations('topbar');
  const { user, logout, updateUser, isAuthenticated, setShowProfileDialog, setShowChangePasswordDialog } = useAuthStore();
  const { locale, setLocale } = useLocaleStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push('/shared');
  };

  // Auto-refresh token balance every 20 seconds when page is visible
  const refreshTokenBalance = async () => {
    const currentUser = useAuthStore.getState().user;
    if (!currentUser) return;
    try {
      const response = await authAPI.getProfile();
      updateUser(response.data);
    } catch (error) {
      console.error('[Header] Failed to refresh token balance:', error);
    }
  };

  useIntervalOnVisible(refreshTokenBalance, isAuthenticated ? 20000 : null);

  const toggleLocale = () => {
    setLocale(locale === 'zh-CN' ? 'en' : 'zh-CN');
  };

  return (
    <header
      className="bg-white/80 backdrop-blur-md px-8 py-3"
      style={{
        boxShadow: "0 1px 3px rgba(79, 70, 229, 0.06), 0 8px 24px rgba(79, 70, 229, 0.04)"
      }}
    >
      <div className="flex items-center justify-between gap-8">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 hover:opacity-90 transition-opacity" aria-label={t('backToHome')}>
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

        {/* Token余额显示 + Account Avatar */}
        <div className="flex items-center gap-3">
          {/* Token Balance Button */}
          <Button
            variant="ghost"
            className="bg-indigo-50/80 hover:bg-indigo-100 gap-1.5 h-8 px-3 rounded-xl"
          >
            <Zap className="h-3.5 w-3.5 text-indigo-600" />
            <span className={cn(
              "text-sm font-medium",
              (user?.token_balance ?? 0) > 0 ? "text-indigo-600" : "text-orange-500"
            )}>
              {user?.token_balance ?? 0}
            </span>
          </Button>

          {/* Account Avatar with Dropdown Menu - Claymorphism Style */}
          <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded-full p-1 bg-indigo-50/80 hover:bg-indigo-100 transition-all"
              aria-label={t('userMenu')}
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
              onClick={() => setShowProfileDialog(true)}
            >
              <User className="mr-2 h-4 w-4" />
              {t('profile')}
            </DropdownMenuItem>
            <DropdownMenuItem
              className="cursor-pointer"
              onClick={() => setShowChangePasswordDialog(true)}
            >
              <Lock className="mr-2 h-4 w-4" />
              {t('changePassword')}
            </DropdownMenuItem>
            {user?.is_admin && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="cursor-pointer text-violet-600 focus:text-violet-600"
                  onClick={() => router.push('/admin/users')}
                >
                  <Shield className="mr-2 h-4 w-4" />
                  {t('adminConsole')}
                </DropdownMenuItem>
              </>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="cursor-pointer"
              onClick={toggleLocale}
            >
              <Globe className="mr-2 h-4 w-4" />
              {locale === 'zh-CN' ? 'English' : '中文'}
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
