"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Settings, LogOut, Zap, Globe, Shield } from "lucide-react";
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
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
} from "@/components/ui/dropdown-menu";
import { useTranslations } from "next-intl";
import { localeNames, locales, type Locale } from "@/i18n";

export function Header() {
  const t = useTranslations('topbar');
  const { user, logout, updateUser, isAuthenticated } = useAuthStore();
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

  return (
    <header
      className="bg-gradient-to-r from-white via-indigo-50/30 to-white border-b-2 border-indigo-100 px-8 py-3"
      style={{
        boxShadow: "0 4px 0 rgba(79, 70, 229, 0.08), 0 8px 16px rgba(79, 70, 229, 0.05)"
      }}
    >
      <div className="flex items-center justify-between gap-8">
        {/* Logo - Claymorphism Style */}
        <Link href="/" className="flex items-center gap-2 hover:opacity-90 transition-opacity" aria-label="返回首页">
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

          {/* Account Avatar with Dropdown Menu - Claymorphism Style */}
          <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 rounded-full p-1 bg-gradient-to-br from-indigo-100 to-indigo-50 border-2 border-indigo-200 hover:shadow-md transition-all"
              style={{
                boxShadow: "0 2px 0 rgba(79, 70, 229, 0.15), 0 4px 8px rgba(79, 70, 229, 0.1)"
              }}
              aria-label="用户菜单"
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
              onClick={() => router.push("/settings")}
            >
              <Settings className="mr-2 h-4 w-4" />
              {t('settings')}
            </DropdownMenuItem>
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>
                <Globe className="mr-2 h-4 w-4" />
                {t('language')}
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent>
                <DropdownMenuRadioGroup value={locale} onValueChange={(value) => setLocale(value as Locale)}>
                  {locales.map((loc) => (
                    <DropdownMenuRadioItem key={loc} value={loc}>
                      {localeNames[loc]}
                    </DropdownMenuRadioItem>
                  ))}
                </DropdownMenuRadioGroup>
              </DropdownMenuSubContent>
            </DropdownMenuSub>
            {user?.is_admin && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="cursor-pointer text-violet-600 focus:text-violet-600"
                  onClick={() => router.push('/admin/users')}
                >
                  <Shield className="mr-2 h-4 w-4" />
                  管理控制台
                </DropdownMenuItem>
              </>
            )}
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