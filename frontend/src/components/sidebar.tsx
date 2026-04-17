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
  Bot,
  Blocks,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { QuickCallDialog } from "@/components/QuickCallDialog";
import { OrganizationSwitcher } from "@/components/OrganizationSwitcher";
import { useTranslations } from "next-intl";
import { useAuthStore } from "@/lib/store";

interface NavItemProps {
  icon: React.ReactNode;
  label: string;
  href: string;
  active?: boolean;
}

function NavItem({ icon, label, href, active }: NavItemProps) {
  return (
    <Link
      href={href}
      className={cn(
        "relative w-full px-4 py-2.5 rounded-full text-sm font-medium flex items-center gap-3 transition-all duration-200 cursor-pointer",
        active
          ? "bg-[#1f1f1f] text-white font-bold"
          : "text-[#b3b3b3] hover:bg-[#1f1f1f] hover:text-white"
      )}
    >
      <span className={cn("transition-colors", active ? "text-[#1ed760]" : "text-[#b3b3b3]")}>
        {icon}
      </span>
      {label}
    </Link>
  );
}

function SidebarContent() {
  const pathname = usePathname();
  const t = useTranslations('sidebar');
  const tQuickCall = useTranslations('quickCall');
  const { currentOrganization, myOrganizations, isAuthenticated } = useAuthStore();
  const isOrgOwner = !!currentOrganization && (myOrganizations?.owned.some(o => o.id === currentOrganization.id) ?? false);

  const mainNavItems = [
    { icon: <Store className="w-4 h-4" />, label: t('marketplace'), href: "/marketplace" },
    { icon: <Bot className="w-4 h-4" />, label: t('claws'), href: "/claws" },
    { icon: <Blocks className="w-4 h-4" />, label: t('myShared'), href: "/shared" },
    { icon: <Key className="w-4 h-4" />, label: t('apiKeys'), href: "/api-keys" },
    { icon: <BarChart3 className="w-4 h-4" />, label: t('usage'), href: "/usage" },
  ];

  return (
    <div className="flex flex-col h-full py-3 px-2">
      {/* Organization Switcher */}
      {isAuthenticated && (
        <div className="px-1 mb-2">
          <OrganizationSwitcher variant="sidebar" />
        </div>
      )}

      {/* Quick Call Button */}
      <QuickCallDialog>
        <Button
          className="w-full mb-3"
        >
          <Sparkles className="w-4 h-4 mr-1.5" />
          {tQuickCall('quickCall')}
        </Button>
      </QuickCallDialog>

      {/* Main Navigation */}
      <nav className="flex-1 flex flex-col space-y-0.5">
        {mainNavItems.map((item) => (
          <NavItem
            key={item.href}
            icon={item.icon}
            label={item.label}
            href={item.href}
            active={pathname === item.href}
          />
        ))}

        {isOrgOwner && (
          <>
            <div className="border-t border-[#282828] my-2 mx-1" />
            <NavItem
              icon={<Users className="w-4 h-4" />}
              label={t('myTeam')}
              href="/my-team"
              active={pathname === '/my-team'}
            />
          </>
        )}
      </nav>

      {/* Bottom Actions */}
      <div className="space-y-2 pt-2">
      </div>
    </div>
  );
}

export function Sidebar() {
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  return (
    <>
      {/* Desktop Sidebar Content - 已在 layout.tsx 中设置 fixed */}
      <div className="hidden lg:block h-full">
        <SidebarContent />
      </div>

      {/* Mobile Menu Button */}
      <button
        className="lg:hidden fixed top-20 left-4 z-50 p-2.5 bg-[#181818] rounded-xl shadow-md border border-[#282828] hover:bg-[#1f1f1f] transition-colors cursor-pointer"
        onClick={() => setIsMobileOpen(!isMobileOpen)}
      >
        {isMobileOpen ? <X className="w-4 h-4 text-[#b3b3b3]" /> : <Menu className="w-4 h-4 text-[#b3b3b3]" />}
      </button>

      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <aside
        className={cn(
          "lg:hidden fixed top-16 left-0 bottom-0 z-50 w-56 flex flex-col bg-[#181818] border-r border-[#282828] transform transition-transform duration-200 ease-in-out shadow-xl",
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <SidebarContent />
      </aside>
    </>
  );
}
