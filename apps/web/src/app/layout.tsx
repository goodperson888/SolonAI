import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { WalletProvider } from '@/components/wallet/WalletProvider'
import { QueryProvider } from '@/components/providers/QueryProvider'
import { I18nProvider } from '@/hooks/useTranslation'
import { Header } from '@/components/layout/Header'
import { Footer } from '@/components/layout/Footer'
import { FloatingAIButton } from '@/components/chat/FloatingAIButton'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Solon AI - Solana生态AI金融智能体',
  description: 'Solana生态全链路非托管AI金融智能体，你的链上资产专属管家',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <I18nProvider>
          <QueryProvider>
            <WalletProvider>
              <Header />
              <main className="min-h-screen">{children}</main>
              <Footer />
              <FloatingAIButton />
            </WalletProvider>
          </QueryProvider>
        </I18nProvider>
      </body>
    </html>
  )
}
