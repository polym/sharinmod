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
  LayoutGrid,
  Cpu,
  Bot,
  Sliders
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
        "w-full px-3 py-2 rounded-md text-sm font-medium flex items-center gap-2.5 transition-colors",
        active
          ? "bg-indigo-50 text-indigo-700"
          : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
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
    { icon: <Bot className="w-4 h-4" />, label: t('claws'), href: "/claws" },
    { icon: <Users className="w-4 h-4" />, label: t('myShared'), href: "/shared" },
    { icon: <Key className="w-4 h-4" />, label: t('apiKeys'), href: "/api-keys" },
    { icon: <BarChart3 className="w-4 h-4" />, label: t('usage'), href: "/usage" },
    { icon: <Settings className="w-4 h-4" />, label: t('settings'), href: "/settings" },
  ];

  const adminNavItems = [
    { icon: <Users className="w-4 h-4" />, label: t('adminUsers'), href: "/admin/users" },
    { icon: <LayoutGrid className="w-4 h-4" />, label: t('adminProviders'), href: "/admin/providers" },
    { icon: <Cpu className="w-4 h-4" />, label: t('adminModels'), href: "/admin/models" },
    { icon: <Sliders className="w-4 h-4" />, label: t('adminSettings'), href: "/admin/settings" },
  ];

  const SidebarContent = () => (
    <div className="flex flex-col h-full pt-0 pl-3 pr-2 pb-4">
      {/* Launch Button - Claymorphism Style */}
      <QuickCallDialog>
        <Button
          className="w-full mt-4 mb-4 bg-indigo-600 hover:bg-indigo-700 text-white flex items-center justify-center rounded-md text-sm font-medium"
        >
          <Sparkles className="w-4 h-4 mr-1.5" />
          {tQuickCall('quickCall')}
        </Button>
      </QuickCallDialog>

      {/* Main Navigation */}
      <nav className="flex flex-col space-y-2">
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
            <div className="border-t border-gray-200 my-2" />
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
      {/* Desktop Sidebar Content - 已在 layout.tsx 中设置 fixed */}
      <div className="hidden lg:block h-full">
        <SidebarContent />
      </div>

      {/* Mobile Menu Button */}
      <button
        className="lg:hidden fixed top-20 left-4 z-50 p-2.5 bg-white rounded-md shadow border border-gray-200 hover:bg-gray-50 transition-colors"
        onClick={() => setIsMobileOpen(!isMobileOpen)}
      >
        {isMobileOpen ? <X className="w-4 h-4 text-gray-600" /> : <Menu className="w-4 h-4 text-gray-600" />}
      </button>

      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Mobile Sidebar - 固定定位，从 Header 下方开始 */}
      <aside
        className={cn(
          "lg:hidden fixed top-16 left-0 bottom-0 z-50 w-56 flex flex-col bg-white border-r border-gray-200 transform transition-transform duration-200 ease-in-out shadow-lg",
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <SidebarContent />
      </aside>
    </>
  );
}
