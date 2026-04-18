'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { WalletMultiButton } from '@solana/wallet-adapter-react-ui'
import { useTranslation } from '@/hooks/useTranslation'

export const Header = () => {
  const pathname = usePathname()
  const { t, locale, setLocale } = useTranslation()

  const navigation = [
    { name: t('nav.dashboard'), href: '/dashboard' },
    { name: t('nav.strategy'), href: '/strategy' },
    { name: 'AI 助手', href: '/ai' },
    { name: '风控中心', href: '/risk' },
  ]

  const toggleLanguage = () => {
    setLocale(locale === 'zh' ? 'en' : 'zh')
  }

  return (
    <header className="sticky top-0 z-50 border-b border-gray-800 bg-gray-950/80 backdrop-blur-lg">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600">
              <span className="text-xl font-bold text-white">S</span>
            </div>
            <span className="text-xl font-bold text-white">Solon AI</span>
          </Link>

          {/* Navigation */}
          <nav className="hidden items-center space-x-8 md:flex">
            {navigation.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`text-sm font-medium transition-colors ${
                  pathname === item.href ? 'text-indigo-400' : 'text-gray-400 hover:text-white'
                }`}
              >
                {item.name}
              </Link>
            ))}
          </nav>

          {/* Right side */}
          <div className="flex items-center space-x-4">
            {/* Language Toggle */}
            <button
              onClick={toggleLanguage}
              className="text-sm text-gray-400 transition-colors hover:text-white"
            >
              {locale === 'zh' ? 'EN' : '中文'}
            </button>

            {/* Wallet Button */}
            <WalletMultiButton />
          </div>
        </div>
      </div>
    </header>
  )
}
