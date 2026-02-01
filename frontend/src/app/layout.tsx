import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Sidebar } from '@/components/sidebar'
import { Header } from '@/components/header'
import { Toaster } from '@/components/ui/toast'
import { LoginDialog } from '@/components/LoginDialog'

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
    <html lang="en">
      <body className={inter.className}>
        <Toaster />
        <LoginDialog />
        <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-purple-50">
          {/* Header spans full width at top */}
          <Header />

          {/* Sidebar and main content below header */}
          <div className="flex">
            <Sidebar />
            <main className="flex-1 overflow-auto">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  )
}
