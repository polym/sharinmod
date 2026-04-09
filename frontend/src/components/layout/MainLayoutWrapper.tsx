'use client';

import { usePathname } from 'next/navigation';
import { Sidebar } from '@/components/sidebar';
import { Header } from '@/components/header';

interface MainLayoutWrapperProps {
  children: React.ReactNode;
}

export function MainLayoutWrapper({ children }: MainLayoutWrapperProps) {
  const pathname = usePathname();
  const isAdminRoute = pathname?.startsWith('/admin');

  if (isAdminRoute) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-purple-50">
      {/* Fixed Header at top */}
      <div className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-sm border-b border-purple-100">
        <Header />
      </div>

      {/* Fixed Sidebar on desktop */}
      <aside className="hidden lg:flex fixed top-16 left-0 bottom-0 w-56 flex-shrink-0 z-40 pt-2">
        <div className="w-full border-r border-gray-200 bg-white">
          <Sidebar />
        </div>
      </aside>

      {/* Main content */}
      <div className="pt-16 lg:pl-56">
        <main className="max-w-7xl mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
