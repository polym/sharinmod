'use client';

import { useState } from 'react';
import { Menu, X } from 'lucide-react';
import { useTranslations } from 'next-intl';
import { Sidebar, PageType } from './Sidebar';
import { TopBar } from './TopBar';
import { cn } from '@/lib/utils';

interface DashboardLayoutProps {
  children: React.ReactNode;
  currentPage: PageType;
  onPageChange: (page: PageType) => void;
}

export function DashboardLayout({ children, currentPage, onPageChange }: DashboardLayoutProps) {
  const t = useTranslations('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handlePageChange = (page: PageType) => {
    onPageChange(page);
    setSidebarOpen(false); // Close sidebar on mobile after navigation
  };

  return (
    <div className="flex h-screen bg-[#121212] overflow-hidden">
      {/* TopBar - 固定在顶部 */}
      <div className="fixed top-0 left-0 right-0 z-50 w-full">
        <TopBar onPageChange={handlePageChange} />
      </div>

      {/* Mobile menu button */}
      <button
        className="md:hidden fixed top-20 left-4 z-50 p-3 rounded-full bg-[#1f1f1f] border border-[#4d4d4d] hover:bg-[#282828] transition-colors cursor-pointer"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label={sidebarOpen ? t('closeMenu') : t('openMenu')}
      >
        {sidebarOpen ? <X className="w-5 h-5 text-white" /> : <Menu className="w-5 h-5 text-white" />}
      </button>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="md:hidden fixed inset-0 z-30 bg-black/70"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar - 固定在左侧，从 TopBar 下方开始 */}
      <div
        className={cn(
          'fixed top-16 left-0 h-[calc(100vh-4rem)]',
          'md:z-50',
          'transform transition-transform duration-200 ease-in-out',
          sidebarOpen ? 'z-50 translate-x-0' : '-translate-x-full md:translate-x-0'
        )}
      >
        <Sidebar currentPage={currentPage} onPageChange={handlePageChange} />
      </div>

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0 pt-16 md:pl-60">
        <main className="flex-1 overflow-auto p-4 md:p-6 bg-[#121212]">
          {children}
        </main>
      </div>
    </div>
  );
}

export type { PageType };
