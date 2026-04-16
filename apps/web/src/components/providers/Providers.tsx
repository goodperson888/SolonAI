'use client'

import dynamic from 'next/dynamic'
import { QueryProvider } from '@/components/providers/QueryProvider'
import { I18nProvider } from '@/hooks/useTranslation'
import { Header } from '@/components/layout/Header'
import { Footer } from '@/components/layout/Footer'
import { FloatingAIButton } from '@/components/chat/FloatingAIButton'

const WalletProviderDynamic = dynamic(
  () =>
    import('@/components/wallet/WalletProvider').then((mod) => ({
      default: mod.WalletProvider,
    })),
  { ssr: false }
)

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <I18nProvider>
      <QueryProvider>
        <WalletProviderDynamic>
          <Header />
          <main className="min-h-screen">{children}</main>
          <Footer />
          <FloatingAIButton />
        </WalletProviderDynamic>
      </QueryProvider>
    </I18nProvider>
  )
}
