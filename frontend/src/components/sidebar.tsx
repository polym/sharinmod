"use client";

import * as React from "react";
import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Store,
  Users,
  Key,
  BarChart3,
  Sparkles,
  Menu,
  X,
  Settings,
  Shield,
  LayoutGrid
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { QuickCallDialog } from "@/components/QuickCallDialog";
import { useTranslations } from "next-intl";
import { useAuthStore } from "@/lib/store";

interface NavItemProps {
  icon: React.ReactNode;
  label: string;
  href: string;
  active?: boolean;
}

interface NavSectionProps {
  children: React.ReactNode;
}

function NavSection({ children }: NavSectionProps) {
  return (
    <div className="mb-4">
      {children}
    </div>
  );
}

function NavItem({ icon, label, href, active }: NavItemProps) {
  return (
    <Link
      href={href}
      className={cn(
        "w-full px-3 py-2 rounded-lg text-sm font-medium flex items-center gap-3 transition-all",
        active
          ? "bg-gradient-to-r from-purple-100 to-purple-50 text-purple-700"
          : "text-gray-600 hover:bg-purple-50 hover:text-purple-600"
      )}
    >
      {icon}
      {label}
    </Link>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const t = useTranslations('sidebar');
  const tQuickCall = useTranslations('quickCall');
  const { user } = useAuthStore();

  const mainNavItems = [
    { icon: <Store className="w-4 h-4" />, label: t('marketplace'), href: "/marketplace" },
    { icon: <Users className="w-4 h-4" />, label: t('myShared'), href: "/shared" },
    { icon: <Key className="w-4 h-4" />, label: t('apiKeys'), href: "/api-keys" },
    { icon: <BarChart3 className="w-4 h-4" />, label: t('usage'), href: "/usage" },
    { icon: <Settings className="w-4 h-4" />, label: t('settings'), href: "/settings" },
  ];

  const adminNavItems = [
    { icon: <Users className="w-4 h-4" />, label: t('adminUsers'), href: "/admin/users" },
    { icon: <LayoutGrid className="w-4 h-4" />, label: t('adminProviders'), href: "/admin/providers" },
  ];

  const SidebarContent = () => (
    <div className="flex flex-col h-full p-4">
      {/* Launch Button */}
      <QuickCallDialog>
        <Button className="w-full mb-4 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white flex items-center justify-center">
          <Sparkles className="w-4 h-4 mr-1.5" />
          {tQuickCall('quickCall')}
        </Button>
      </QuickCallDialog>

      {/* Main Navigation */}
      <nav className="flex flex-col space-y-1">
        <NavSection>
          {mainNavItems.map((item) => (
            <NavItem
              key={item.href}
              icon={item.icon}
              label={item.label}
              href={item.href}
              active={pathname === item.href}
            />
          ))}
        </NavSection>

        {user?.is_admin && (
          <>
            <div className="border-t border-purple-200/50 my-2" />
            <NavSection>
              {adminNavItems.map((item) => (
                <NavItem
                  key={item.href}
                  icon={item.icon}
                  label={item.label}
                  href={item.href}
                  active={pathname === item.href}
                />
              ))}
            </NavSection>
          </>
        )}
      </nav>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar Content - positioned by layout.tsx */}
      <div className="hidden lg:block h-full">
        <SidebarContent />
      </div>

      {/* Mobile Menu Button */}
      <button
        className="lg:hidden fixed top-20 left-4 z-50 p-2 bg-white rounded-lg shadow-md border border-purple-100"
        onClick={() => setIsMobileOpen(!isMobileOpen)}
      >
        {isMobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <aside
        className={cn(
          "lg:hidden fixed top-16 left-0 bottom-0 z-50 w-56 flex flex-col bg-gradient-to-br from-purple-50 via-white to-purple-50 border-r border-purple-100/50 transform transition-transform duration-200 ease-in-out",
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <SidebarContent />
      </aside>
    </>
  );
}
