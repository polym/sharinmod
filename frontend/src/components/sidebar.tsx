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
  X 
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

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
    { icon: <Store className="w-4 h-4" />, label: "广场", href: "/" },
    { icon: <Users className="w-4 h-4" />, label: "我的共享", href: "/shared" },
    { icon: <Key className="w-4 h-4" />, label: "API Keys", href: "/api-keys" },
    { icon: <BarChart3 className="w-4 h-4" />, label: "使用情况", href: "/usage" },
  ];

  const bottomNavItems = [
    { icon: <Grid className="w-4 h-4" />, label: "Activity", href: "/activity" },
    { icon: <Radio className="w-4 h-4" />, label: "Grafana", href: "/grafana" },
  ];

  const SidebarContent = () => (
    <>
      {/* Logo */}
      <div className="flex items-center gap-2 mb-6 px-2">
        <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
          SM
        </div>
        <span className="font-semibold text-gray-900">SharinMod</span>
      </div>

      {/* Organization Selector */}
      <div className="mb-4">
        <div className="text-xs text-gray-500 mb-2 px-2">Organization</div>
        <button className="w-full px-3 py-2 bg-purple-50 hover:bg-purple-100 rounded-lg text-left text-sm flex items-center justify-between transition-colors">
          <div className="flex items-center gap-2">
            <User className="w-4 h-4 text-purple-600" />
            <span>Personal</span>
          </div>
          <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Launch Button */}
      <Button className="w-full mb-4">
        <Sparkles className="w-4 h-4 mr-2" />
        Launch an App
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
        
        <div className="pt-4 mt-4 border-t border-gray-200">
          {bottomNavItems.map((item) => (
            <NavItem
              key={item.href}
              icon={item.icon}
              label={item.label}
              href={item.href}
              active={pathname === item.href}
            />
          ))}
        </div>
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
      <aside className="hidden lg:flex w-56 bg-white border-r border-purple-100 flex-col p-4 h-screen sticky top-0">
        <SidebarContent />
      </aside>

      {/* Mobile Sidebar */}
      <aside 
        className={cn(
          "lg:hidden fixed inset-y-0 left-0 z-50 w-56 bg-white border-r border-purple-100 flex flex-col p-4 transform transition-transform duration-200 ease-in-out",
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <SidebarContent />
      </aside>
    </>
  );
}
