'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { StrategyCard } from '@/components/strategy/StrategyCard'
import { useTranslation } from '@/hooks/useTranslation'
import { useWallet } from '@solana/wallet-adapter-react'
import { strategyApi } from '@/lib/api-client'

export default function StrategyPage() {
  const { t } = useTranslation()
  const { publicKey } = useWallet()
  const [amount, setAmount] = useState('')
  const [selectedToken, setSelectedToken] = useState('USDC')
  const [riskLevel, setRiskLevel] = useState<'conservative' | 'balanced' | 'aggressive'>('balanced')
  const [duration, setDuration] = useState('30')
  const [strategies, setStrategies] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (publicKey) {
      loadStrategies()
    }
  }, [publicKey])

  const loadStrategies = async () => {
    if (!publicKey) return

    setLoading(true)
    try {
      const data = await strategyApi.listStrategies(publicKey.toBase58())
      setStrategies(data.strategies || [])
    } catch (error) {
      console.error('Failed to load strategies:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    if (!publicKey || !amount) return

    setGenerating(true)
    try {
      const _result = await strategyApi.generateStrategy({
        wallet_address: publicKey.toBase58(),
        amount: parseFloat(amount),
        token: selectedToken,
        risk_level: riskLevel,
        duration_days: parseInt(duration),
      })

      // 重新加载策略列表
      await loadStrategies()

      // 清空表单
      setAmount('')
      setDuration('30')
    } catch (error) {
      console.error('Failed to generate strategy:', error)
    } finally {
      setGenerating(false)
    }
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
            <Button
              variant="primary"
              size="lg"
              className="w-full"
              onClick={handleGenerate}
              disabled={!publicKey || !amount || generating}
            >
              {generating ? t('strategy.generating') || '生成中...' : t('strategy.generateButton')}
            </Button>
            {!publicKey && <p className="mt-2 text-center text-sm text-yellow-500">请先连接钱包</p>}
          </div>
        </Card>

        {/* Recommended Strategies */}
        <div>
          <h2 className="mb-6 text-2xl font-bold text-white">{t('strategy.recommended')}</h2>
          {loading ? (
            <div className="text-center text-gray-400">加载中...</div>
          ) : strategies.length > 0 ? (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {strategies.map((strategy) => (
                <StrategyCard key={strategy.id} {...strategy} />
              ))}
            </div>
          ) : (
            <div className="text-center text-gray-400">
              {publicKey ? '暂无策略，点击上方生成按钮创建策略' : '请先连接钱包'}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
