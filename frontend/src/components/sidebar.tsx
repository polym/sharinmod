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
  Cpu
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
        "w-full px-4 py-3 rounded-2xl text-sm font-medium flex items-center gap-3 transition-all border-2 relative",
        active
          ? "bg-gradient-to-br from-indigo-100 to-indigo-50 text-indigo-700 border-indigo-200 shadow-lg"
          : "text-gray-600 hover:bg-white hover:text-indigo-600 hover:shadow-md hover:border-indigo-100 border-transparent"
      )}
      style={active ? {
        boxShadow: "0 4px 0 rgba(79, 70, 229, 0.2), 0 8px 16px rgba(79, 70, 229, 0.1)"
      } : {}}
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
    { icon: <Cpu className="w-4 h-4" />, label: t('adminModels'), href: "/admin/models" },
  ];

  const SidebarContent = () => (
    <div className="flex flex-col h-full p-4">
      {/* Launch Button - Claymorphism Style */}
      <QuickCallDialog>
        <Button
          className="w-full mb-4 bg-gradient-to-br from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white flex items-center justify-center rounded-2xl border-2 border-indigo-300 shadow-lg"
          style={{
            boxShadow: "0 4px 0 rgba(79, 70, 229, 0.3), 0 8px 20px rgba(79, 70, 229, 0.2)"
          }}
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
            <div className="border-t-2 border-indigo-200/50 my-2" />
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

      {/* Mobile Menu Button - Claymorphism Style */}
      <button
        className="lg:hidden fixed top-20 left-4 z-50 p-3 bg-white rounded-2xl shadow-lg border-2 border-indigo-100 hover:shadow-xl transition-all"
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        style={{
          boxShadow: "0 4px 0 rgba(79, 70, 229, 0.15), 0 8px 16px rgba(79, 70, 229, 0.1)"
        }}
      >
        {isMobileOpen ? <X className="w-5 h-5 text-indigo-600" /> : <Menu className="w-5 h-5 text-indigo-600" />}
      </button>

      {/* Mobile Overlay */}
      {isMobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Mobile Sidebar - Claymorphism Style */}
      <aside
        className={cn(
          "lg:hidden fixed top-16 left-0 bottom-0 z-50 w-56 flex flex-col bg-gradient-to-br from-indigo-50 via-white to-indigo-50 border-r-2 border-indigo-100 transform transition-transform duration-200 ease-in-out",
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
        style={{
          boxShadow: "4px 0 16px rgba(79, 70, 229, 0.1)"
        }}
      >
        <SidebarContent />
      </aside>
    </>
  );
}
