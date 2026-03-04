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
      {/* TopBar - 固定在顶部 */}
      <div className="fixed top-0 left-0 right-0 z-50 w-full">
        <TopBar onPageChange={handlePageChange} />
      </div>

      {/* Mobile menu button - Claymorphism Style */}
      <button
        className="md:hidden fixed top-20 left-4 z-50 p-4 rounded-2xl bg-white shadow-lg border-2 border-indigo-100 hover:shadow-xl transition-all"
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

      {/* Sidebar - 固定在左侧，从 TopBar 下方开始 */}
      <div
        className={cn(
          'fixed top-16 left-0 h-[calc(100vh-4rem)]',
          'md:z-50', // 桌面端提高 z-index，避免被 TopBar 遮挡
          'transform transition-transform duration-200 ease-in-out',
          sidebarOpen ? 'z-50 translate-x-0' : '-translate-x-full md:translate-x-0'
        )}
      >
        <Sidebar currentPage={currentPage} onPageChange={handlePageChange} />
      </div>

      {/* Main content area - 滚动区域，预留 TopBar 和 Sidebar 空间 */}
      <div className="flex-1 flex flex-col min-w-0 pt-16 md:pl-60">
        <main className="flex-1 overflow-auto p-4 md:p-6 bg-gradient-to-br from-indigo-50/50 via-transparent to-indigo-50/30">
          {children}
        </main>
      </div>
    </div>
  );
}

export type { PageType };
