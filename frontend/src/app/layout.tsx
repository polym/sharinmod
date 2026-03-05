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

            {/* Fixed Sidebar on desktop - 从 Header 下方开始 */}
            <aside className="hidden lg:flex fixed top-16 left-0 bottom-0 w-56 flex-shrink-0 z-40 pt-2">
              <div className="w-full border-r border-gray-200 bg-white">
                <Sidebar />
              </div>
            </aside>

            {/* Main content - 预留 Header 和 Sidebar 空间 */}
            <div className="pt-16 lg:pl-56">
              <main className="max-w-7xl mx-auto">
                {children}
              </main>
            </div>
          </div>
        </I18nProvider>
      </body>
    </html>
  )
}
