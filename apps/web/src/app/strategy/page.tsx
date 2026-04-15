'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { StrategyCard } from '@/components/strategy/StrategyCard'
import { useTranslation } from '@/hooks/useTranslation'
import { mockStrategies } from '@/data/mockStrategies'

export default function StrategyPage() {
  const { t } = useTranslation()
  const [amount, setAmount] = useState('')
  const [selectedToken, setSelectedToken] = useState('USDC')
  const [riskLevel, setRiskLevel] = useState<'conservative' | 'balanced' | 'aggressive'>('balanced')
  const [duration, setDuration] = useState('30')

  const handleGenerate = () => {
    // TODO: 调用后端API生成策略
    void { amount, selectedToken, riskLevel, duration }
  }

  return (
    <div className="min-h-screen bg-gray-950 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Page Title */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">{t('strategy.title')}</h1>
          <p className="mt-2 text-gray-400">根据你的风险偏好，AI为你生成最优策略</p>
        </div>

        {/* Strategy Generator Form */}
        <Card className="mb-8">
          <h2 className="mb-6 text-xl font-semibold text-white">{t('strategy.generate')}</h2>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {/* Amount Input */}
            <div>
              <Input
                label={t('strategy.amount')}
                type="number"
                placeholder="1000"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
            </div>

            {/* Token Select */}
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-300">
                {t('strategy.token')}
              </label>
              <select
                value={selectedToken}
                onChange={(e) => setSelectedToken(e.target.value)}
                className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="SOL">SOL</option>
                <option value="USDC">USDC</option>
                <option value="USDT">USDT</option>
              </select>
            </div>

            {/* Risk Level */}
            <div className="md:col-span-2">
              <label className="mb-3 block text-sm font-medium text-gray-300">
                {t('strategy.riskLevel')}
              </label>
              <div className="grid grid-cols-3 gap-4">
                <button
                  onClick={() => setRiskLevel('conservative')}
                  className={`rounded-lg border-2 p-4 transition-all ${
                    riskLevel === 'conservative'
                      ? 'border-green-500 bg-green-500/10'
                      : 'border-gray-700 hover:border-gray-600'
                  }`}
                >
                  <div className="mb-2 text-2xl">🛡️</div>
                  <p className="font-medium text-white">{t('strategy.conservative')}</p>
                  <p className="mt-1 text-sm text-gray-400">5-8% APY</p>
                </button>

                <button
                  onClick={() => setRiskLevel('balanced')}
                  className={`rounded-lg border-2 p-4 transition-all ${
                    riskLevel === 'balanced'
                      ? 'border-yellow-500 bg-yellow-500/10'
                      : 'border-gray-700 hover:border-gray-600'
                  }`}
                >
                  <div className="mb-2 text-2xl">⚖️</div>
                  <p className="font-medium text-white">{t('strategy.balanced')}</p>
                  <p className="mt-1 text-sm text-gray-400">10-15% APY</p>
                </button>

                <button
                  onClick={() => setRiskLevel('aggressive')}
                  className={`rounded-lg border-2 p-4 transition-all ${
                    riskLevel === 'aggressive'
                      ? 'border-red-500 bg-red-500/10'
                      : 'border-gray-700 hover:border-gray-600'
                  }`}
                >
                  <div className="mb-2 text-2xl">🚀</div>
                  <p className="font-medium text-white">{t('strategy.aggressive')}</p>
                  <p className="mt-1 text-sm text-gray-400">20%+ APY</p>
                </button>
              </div>
            </div>

            {/* Duration */}
            <div className="md:col-span-2">
              <Input
                label={`${t('strategy.duration')} (${t('strategy.days')})`}
                type="number"
                placeholder="30"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
              />
            </div>
          </div>

          <div className="mt-6">
            <Button variant="primary" size="lg" className="w-full" onClick={handleGenerate}>
              {t('strategy.generateButton')}
            </Button>
          </div>
        </Card>

        {/* Recommended Strategies */}
        <div>
          <h2 className="mb-6 text-2xl font-bold text-white">{t('strategy.recommended')}</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {mockStrategies.map((strategy) => (
              <StrategyCard key={strategy.id} {...strategy} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
