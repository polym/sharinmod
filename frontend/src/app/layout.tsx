import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Sidebar } from '@/components/sidebar'
import { Header } from '@/components/header'
import { Toaster } from '@/components/ui/toast'
import { LoginDialog } from '@/components/LoginDialog'
import { I18nProvider } from '@/lib/i18n-provider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'SharinMod - API Token Sharing Platform',
  description: 'Share and manage your API tokens with the community',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <I18nProvider>
          <Toaster />
          <LoginDialog />
          <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-purple-50">
            {/* Fixed Header at top */}
            <div className="fixed top-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-sm border-b border-purple-100">
              <Header />
            </div>

            {/* Sidebar and main content below fixed header */}
            <div className="flex pt-16">
              {/* Fixed Sidebar on desktop */}
              <div className="hidden lg:block">
                <div className="fixed left-0 top-16 bottom-0 w-56 bg-gradient-to-br from-purple-50 via-white to-purple-50 border-r border-purple-100/50">
                  <Sidebar />
                </div>
              </div>

              {/* Main content with left padding for fixed sidebar */}
              <main className="flex-1 lg:ml-56 min-h-screen">
                {children}
              </main>
            </div>
          </div>
        </I18nProvider>
      </body>
    </html>
  )
}
