'use client'

import dynamic from 'next/dynamic'
import { usePathname } from 'next/navigation'
import { QueryProvider } from '@/components/providers/QueryProvider'
import { I18nProvider } from '@/hooks/useTranslation'
import { Header } from '@/components/layout/Header'
import { Footer } from '@/components/layout/Footer'
import { FloatingAIButton } from '@/components/chat/FloatingAIButton'
import { NetworkProvider } from '@/components/wallet/NetworkContext'

const WalletProviderDynamic = dynamic(
  () =>
    import('@/components/wallet/WalletProvider').then((mod) => ({
      default: mod.WalletProvider,
    })),
  { ssr: false }
)

export default function Providers({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const hideFooter = pathname === '/ai'
  const isAIPage = pathname === '/ai'

  return (
    <I18nProvider>
      <QueryProvider>
        <NetworkProvider>
          <WalletProviderDynamic>
            <div className={isAIPage ? 'flex h-screen flex-col overflow-hidden' : ''}>
              <Header />
              <main className={isAIPage ? 'flex-1 overflow-hidden' : 'min-h-screen'}>
                {children}
              </main>
              {!hideFooter && <Footer />}
            </div>
            <FloatingAIButton />
          </WalletProviderDynamic>
        </NetworkProvider>
      </QueryProvider>
    </I18nProvider>
  )
}

// 保留命名导出以兼容其他地方的引用
export { Providers }
