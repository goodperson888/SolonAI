'use client'

import { Button } from '@/components/ui/Button'
import { useTranslation } from '@/hooks/useTranslation'

export default function LandingPage() {
  const { t } = useTranslation()

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background Effects */}
        <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10 blur-3xl" />

        <div className="relative mx-auto max-w-7xl px-4 pb-32 pt-20 sm:px-6 lg:px-8">
          <div className="text-center">
            {/* Logo */}
            <div className="mb-8 flex justify-center">
              <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-600 shadow-2xl shadow-indigo-500/50">
                <span className="text-4xl font-bold text-white">S</span>
              </div>
            </div>

            {/* Title */}
            <h1 className="mb-6 text-5xl font-bold text-white md:text-7xl">
              {t('landing.hero.title')}
            </h1>

            {/* Subtitle */}
            <p className="mx-auto mb-12 max-w-3xl text-xl text-gray-400 md:text-2xl">
              {t('landing.hero.subtitle')}
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col items-center justify-center space-y-4 sm:flex-row sm:space-x-6 sm:space-y-0">
              <Button variant="primary" size="lg" className="w-full sm:w-auto">
                {t('landing.hero.cta')}
              </Button>
              <Button variant="outline" size="lg" className="w-full sm:w-auto">
                {t('landing.hero.learnMore')}
              </Button>
            </div>

            {/* Stats */}
            <div className="mx-auto mt-20 grid max-w-3xl grid-cols-3 gap-8">
              <div>
                <p className="mb-2 text-4xl font-bold text-white">$50M+</p>
                <p className="text-sm text-gray-400">管理资产</p>
              </div>
              <div>
                <p className="mb-2 text-4xl font-bold text-white">10K+</p>
                <p className="text-sm text-gray-400">活跃用户</p>
              </div>
              <div>
                <p className="mb-2 text-4xl font-bold text-white">15%</p>
                <p className="text-sm text-gray-400">平均APY</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-gray-900/50 py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-4xl font-bold text-white">{t('landing.features.title')}</h2>
          </div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-4">
            {/* Feature 1 */}
            <div className="rounded-2xl border border-gray-700 bg-gray-800/50 p-8 transition-all hover:border-indigo-500/50">
              <div className="mb-4 text-4xl">🤖</div>
              <h3 className="mb-3 text-xl font-semibold text-white">
                {t('landing.features.ai.title')}
              </h3>
              <p className="text-gray-400">{t('landing.features.ai.description')}</p>
            </div>

            {/* Feature 2 */}
            <div className="rounded-2xl border border-gray-700 bg-gray-800/50 p-8 transition-all hover:border-indigo-500/50">
              <div className="mb-4 text-4xl">🔒</div>
              <h3 className="mb-3 text-xl font-semibold text-white">
                {t('landing.features.nonCustodial.title')}
              </h3>
              <p className="text-gray-400">{t('landing.features.nonCustodial.description')}</p>
            </div>

            {/* Feature 3 */}
            <div className="rounded-2xl border border-gray-700 bg-gray-800/50 p-8 transition-all hover:border-indigo-500/50">
              <div className="mb-4 text-4xl">⚡</div>
              <h3 className="mb-3 text-xl font-semibold text-white">
                {t('landing.features.automated.title')}
              </h3>
              <p className="text-gray-400">{t('landing.features.automated.description')}</p>
            </div>

            {/* Feature 4 */}
            <div className="rounded-2xl border border-gray-700 bg-gray-800/50 p-8 transition-all hover:border-indigo-500/50">
              <div className="mb-4 text-4xl">📊</div>
              <h3 className="mb-3 text-xl font-semibold text-white">
                {t('landing.features.realtime.title')}
              </h3>
              <p className="text-gray-400">{t('landing.features.realtime.description')}</p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-4xl font-bold text-white">{t('landing.howItWorks.title')}</h2>
          </div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
            {[1, 2, 3, 4].map((step) => (
              <div key={step} className="relative">
                <div className="text-center">
                  <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-indigo-600 to-purple-600">
                    <span className="text-2xl font-bold text-white">{step}</span>
                  </div>
                  <h3 className="mb-3 text-xl font-semibold text-white">
                    {t(`landing.howItWorks.step${step}.title`)}
                  </h3>
                  <p className="text-gray-400">{t(`landing.howItWorks.step${step}.description`)}</p>
                </div>
                {step < 4 && (
                  <div className="absolute left-full top-8 -z-10 hidden h-0.5 w-full bg-gradient-to-r from-indigo-600 to-transparent md:block" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gradient-to-r from-indigo-600/20 via-purple-600/20 to-pink-600/20 py-20">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
          <h2 className="mb-6 text-4xl font-bold text-white">{t('landing.cta.title')}</h2>
          <Button variant="primary" size="lg">
            {t('landing.cta.button')}
          </Button>
        </div>
      </section>
    </div>
  )
}
