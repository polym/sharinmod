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
  Grid, 
  Sparkles, 
  Radio, 
  User, 
  Menu, 
  X,
  Settings
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

// Gradient background matching the main app background for visual cohesion
const SIDEBAR_GRADIENT_BG = "bg-gradient-to-br from-purple-50 via-white to-purple-50";

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

  const mainNavItems = [
    { icon: <Store className="w-4 h-4" />, label: "广场", href: "/marketplace" },
    { icon: <Users className="w-4 h-4" />, label: "共享订阅", href: "/shared" },
    { icon: <Key className="w-4 h-4" />, label: "API Keys", href: "/api-keys" },
    { icon: <BarChart3 className="w-4 h-4" />, label: "使用情况", href: "/usage" },
    { icon: <Settings className="w-4 h-4" />, label: "设置", href: "/settings" },
  ];

  const SidebarContent = () => (
    <>
      {/* Launch Button */}
      <Button className="w-full mb-4 bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 text-white">
        <Sparkles className="w-4 h-4 mr-1" />
        即刻调用
      </Button>

      {/* Main Navigation */}
      <nav className="flex-1 space-y-1">
        {mainNavItems.map((item) => (
          <NavItem
            key={item.href}
            icon={item.icon}
            label={item.label}
            href={item.href}
            active={pathname === item.href}
          />
        ))}
      </nav>
    </>
  );

  return (
    <>
      {/* Mobile Menu Button */}
      <button 
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-md border border-purple-100"
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

      {/* Desktop Sidebar */}
      <aside className={cn("hidden lg:flex w-56 flex-col p-4 min-h-screen", SIDEBAR_GRADIENT_BG)}>
        <SidebarContent />
      </aside>

      {/* Mobile Sidebar */}
      <aside 
        className={cn(
          "lg:hidden fixed inset-y-0 left-0 z-50 w-56 flex flex-col p-4 transform transition-transform duration-200 ease-in-out",
          SIDEBAR_GRADIENT_BG,
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <SidebarContent />
      </aside>
    </>
  );
}
