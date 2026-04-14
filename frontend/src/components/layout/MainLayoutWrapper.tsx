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
    <div className="min-h-screen bg-clay-background">
      {/* Fixed Header at top */}
      <div className="fixed top-0 left-0 right-0 z-50">
        <Header />
      </div>

      {/* Fixed Sidebar on desktop */}
      <aside className="hidden lg:flex fixed top-16 left-0 bottom-0 w-56 flex-shrink-0 z-40 bg-white border-r border-indigo-100/80">
        <div className="w-full">
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
