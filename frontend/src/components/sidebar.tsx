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
  Building2,
  ArrowRight,
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
        "relative w-full px-3 py-2.5 rounded-lg text-sm font-medium flex items-center gap-3 transition-all duration-200 cursor-pointer",
        active
          ? "bg-indigo-50 text-indigo-700 font-semibold"
          : "text-gray-500 hover:bg-indigo-50/60 hover:text-indigo-600"
      )}
    >
      {active && (
        <span className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 bg-indigo-500 rounded-r-full" />
      )}
      <span className={cn("transition-colors", active ? "text-indigo-600" : "text-gray-400 group-hover:text-indigo-500")}>
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
  const { currentOrganization, myOrganizations, isAuthenticated, setShowCreateOrganizationDialog } = useAuthStore();
  const isOrgOwner = !!currentOrganization && (myOrganizations?.owned.some(o => o.id === currentOrganization.id) ?? false);
  const hasNoOrg = isAuthenticated && !currentOrganization;

  const mainNavItems = [
    { icon: <Store className="w-4 h-4" />, label: t('marketplace'), href: "/marketplace" },
    { icon: <Bot className="w-4 h-4" />, label: t('claws'), href: "/claws" },
    { icon: <Users className="w-4 h-4" />, label: t('myShared'), href: "/shared" },
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
          className="w-full mb-3 bg-indigo-600 hover:bg-indigo-700 text-white flex items-center justify-center rounded-lg text-sm font-medium cursor-pointer"
          style={{ boxShadow: "0 2px 0 rgba(67,56,202,0.5), 0 4px 12px rgba(79,70,229,0.25)" }}
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
            <div className="border-t border-indigo-100 my-2 mx-1" />
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
        {/* Private Registry CTA - guide users to create their own space */}
        {hasNoOrg && (
          <div className="rounded-lg bg-gradient-to-br from-indigo-50 via-violet-50/60 to-indigo-50 border border-indigo-100 p-3">
            <div className="flex items-start gap-2 mb-2.5">
              <div
                className="w-7 h-7 rounded-md bg-indigo-600 flex items-center justify-center flex-shrink-0"
                style={{ boxShadow: "0 2px 0 rgba(67,56,202,0.4), 0 4px 8px rgba(79,70,229,0.25)" }}
              >
                <Building2 className="w-3.5 h-3.5 text-white" />
              </div>
              <div>
                <p className="text-xs font-semibold text-indigo-900 leading-tight">{t('privateServerTitle')}</p>
                <p className="text-[11px] text-indigo-500 mt-0.5 leading-relaxed">{t('privateServerDesc')}</p>
              </div>
            </div>
            <button
              onClick={() => setShowCreateOrganizationDialog(true)}
              className="w-full flex items-center justify-center gap-1 text-xs py-1.5 px-3 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white rounded-md font-medium transition-colors cursor-pointer"
            >
              {t('createNow')}
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>
        )}
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
        className="lg:hidden fixed top-20 left-4 z-50 p-2.5 bg-white rounded-xl shadow-md border border-indigo-100 hover:bg-indigo-50 transition-colors cursor-pointer"
        onClick={() => setIsMobileOpen(!isMobileOpen)}
      >
        {isMobileOpen ? <X className="w-4 h-4 text-indigo-600" /> : <Menu className="w-4 h-4 text-indigo-600" />}
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
          "lg:hidden fixed top-16 left-0 bottom-0 z-50 w-56 flex flex-col bg-white border-r border-indigo-100 transform transition-transform duration-200 ease-in-out shadow-xl",
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <SidebarContent />
      </aside>
    </>
  );
}
