'use client';

import { useState } from 'react';
import { Menu, X } from 'lucide-react';
import { Sidebar, PageType } from './Sidebar';
import { TopBar } from './TopBar';
import { cn } from '@/lib/utils';

interface DashboardLayoutProps {
  children: React.ReactNode;
  currentPage: PageType;
  onPageChange: (page: PageType) => void;
}

export function DashboardLayout({ children, currentPage, onPageChange }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handlePageChange = (page: PageType) => {
    onPageChange(page);
    setSidebarOpen(false); // Close sidebar on mobile after navigation
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-indigo-50 via-white to-indigo-50 overflow-hidden">
      {/* Mobile menu button - Claymorphism Style */}
      <button
        className="md:hidden fixed top-4 left-4 z-50 p-3 rounded-2xl bg-white shadow-lg border-2 border-indigo-100 hover:shadow-xl transition-all"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label={sidebarOpen ? '关闭菜单' : '打开菜单'}
        style={{
          boxShadow: "0 4px 0 rgba(79, 70, 229, 0.15), 0 8px 16px rgba(79, 70, 229, 0.1)"
        }}
      >
        {sidebarOpen ? <X className="w-5 h-5 text-indigo-600" /> : <Menu className="w-5 h-5 text-indigo-600" />}
      </button>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="md:hidden fixed inset-0 z-30 bg-black/30 backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={cn(
          'fixed md:static inset-y-0 left-0 z-40',
          'transform transition-transform duration-200 ease-in-out',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        )}
      >
        <Sidebar currentPage={currentPage} onPageChange={handlePageChange} />
      </div>

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar onPageChange={handlePageChange} />
        <main className="flex-1 overflow-auto p-4 md:p-6 bg-gradient-to-br from-indigo-50/50 via-transparent to-indigo-50/30">
          {children}
        </main>
      </div>
    </div>
  );
}

export type { PageType };
