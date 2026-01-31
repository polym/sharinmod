"use client";

import * as React from "react";
import Link from "next/link";
import { useAuthStore } from "@/lib/store";
import { UserAvatar } from "@/components/UserAvatar";

export function Header() {
  const { user } = useAuthStore();

  // Simplified header: Logo moved from sidebar to header, navigation simplified to account avatar only
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

        {/* Account Avatar */}
        <Link href="/settings" className="transition-opacity hover:opacity-90">
          <UserAvatar
            email={user?.email}
            name={user?.name}
            avatar_url={user?.avatar_url}
            className="h-8 w-8"
          />
        </Link>
      </div>
    </header>
  );
}
