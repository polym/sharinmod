import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Toaster } from '@/components/ui/toast'
import { LoginDialog } from '@/components/LoginDialog'
import { ChangePasswordDialog } from '@/components/ChangePasswordDialog'
import { ChangePasswordDialogFromMenu } from '@/components/ChangePasswordDialogFromMenu'
import { ResetPasswordDialog } from '@/components/ResetPasswordDialog'
import { CreateOrganizationDialog } from '@/components/CreateOrganizationDialog'
import { ProfileDialog } from '@/components/ProfileDialog'
import { I18nProvider } from '@/lib/i18n-provider'
import { MainLayoutWrapper } from '@/components/layout/MainLayoutWrapper'

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
          <ChangePasswordDialog />
          <ChangePasswordDialogFromMenu />
          <ResetPasswordDialog />
          <CreateOrganizationDialog />
          <ProfileDialog />
          <MainLayoutWrapper>
            {children}
          </MainLayoutWrapper>
        </I18nProvider>
      </body>
    </html>
  )
}
