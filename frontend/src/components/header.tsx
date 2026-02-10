"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Settings, LogOut, Zap } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/store";
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
  const { user, logout, updateUser, isAuthenticated } = useAuthStore();
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
    <header className="bg-white border-b border-purple-100 px-8 py-4">
      <div className="flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 hover:opacity-90 transition-opacity" aria-label="返回首页">
          <div className="w-7 h-7 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-xs">
            SM
          </div>
          <span className="font-semibold text-gray-900 text-sm">SharinMod</span>
        </Link>

        {/* Token余额显示 + Account Avatar */}
        <div className="flex items-center gap-3">
          <Button variant="ghost" className="bg-brand-100 gap-1.5 h-8 px-3 rounded-full">
            <Zap className="h-3.5 w-3.5 text-brand-500" />
            <span className={cn(
              "text-sm font-medium",
              (user?.token_balance ?? 0) > 0 ? "text-brand-500" : "text-red-600"
            )}>
              {user?.token_balance ?? 0}
            </span>
          </Button>

          {/* Account Avatar with Dropdown Menu */}
          <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className="focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 rounded-full transition-opacity hover:opacity-90"
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
