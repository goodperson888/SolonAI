'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { StrategyCard } from '@/components/strategy/StrategyCard'
import { useTranslation } from '@/hooks/useTranslation'
import { useWallet } from '@solana/wallet-adapter-react'
import { strategyApi, type Strategy, type StrategyCapabilitiesResponse } from '@/lib/api-client'
import { useSolanaNetwork } from '@/components/wallet/NetworkContext'

export default function StrategyPage() {
  const { t } = useTranslation()
  const { publicKey } = useWallet()
  const { network } = useSolanaNetwork()
  const [amount, setAmount] = useState('')
  const [selectedToken, setSelectedToken] = useState('USDC')
  const [riskLevel, setRiskLevel] = useState<'conservative' | 'balanced' | 'aggressive'>('balanced')
  const [duration, setDuration] = useState('30')
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [capabilities, setCapabilities] = useState<StrategyCapabilitiesResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [showQuickGenerator, setShowQuickGenerator] = useState(false)

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (publicKey) {
      loadStrategies()
    }
    loadCapabilities()
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

  const loadCapabilities = async () => {
    try {
      const data = await strategyApi.getCapabilities()
      setCapabilities(data)
    } catch (error) {
      console.error('Failed to load capabilities:', error)
    }
  }

  const getExecutionPresentation = (strategy: Strategy) => {
    const protocolKey = (strategy.protocol_name || '').toLowerCase()
    const capability = capabilities?.protocols?.[protocolKey]
    const realExecutable =
      capability?.wallet_signature && network === 'mainnet' && !capabilities?.demo_mode
    const previewOnly = capability && !capability.wallet_signature

    let executionLabel = '查看执行详情'
    let executionHint = '进入详情页查看执行结果、费用估计和下一步动作。'

    if (capabilities?.demo_mode) {
      executionLabel = '查看演示预览'
      executionHint = '当前为 DEMO 演示模式，适合完整展示流程，不会直接拉起真实签名。'
    } else if (realExecutable) {
      executionLabel = '尝试拉起钱包'
      executionHint = '当前协议支持主网签名链路，可在详情页尝试生成待签名交易。'
    } else if (network === 'devnet') {
      executionLabel = '查看开发网预览'
      executionHint = '当前网络为 devnet，默认优先展示执行预览与风险确认。'
    } else if (previewOnly) {
      executionLabel = '查看参数预览'
      executionHint = capability.notes
    }

    return {
      executionLabel,
      executionHint,
      primaryActionLabel: executionLabel,
      statusLabel: `状态 · ${strategy.status}`,
    }
  }

  // 转换后端数据到 StrategyCard props 格式
  const convertStrategyToCardProps = (strategy: Strategy) => {
    const riskLevelMap: Record<string, 'low' | 'medium' | 'high'> = {
      conservative: 'low',
      balanced: 'medium',
      aggressive: 'high',
    }

    return {
      id: strategy.id,
      name: strategy.title || '未命名策略',
      protocol: strategy.protocol_name || '未知协议',
      expectedAPY: strategy.estimated_apy || 0,
      riskLevel: riskLevelMap[strategy.risk_level] || 'medium',
      lockPeriod: '灵活',
      steps: strategy.steps?.map((s) => s.description || s.action || '') || [],
      deployed: strategy.status === 'approved' || strategy.status === 'executed',
      deployedAmount: strategy.input_amount || 0,
      detailsHref: `/strategy/${strategy.id}`,
      actionHref: `/strategy/${strategy.id}`,
      ...getExecutionPresentation(strategy),
    }
  }

  const activeStrategies = strategies.filter(
    (strategy) => strategy.status === 'approved' || strategy.status === 'executed'
  )
  const draftStrategies = strategies.filter(
    (strategy) => strategy.status !== 'approved' && strategy.status !== 'executed'
  )
  const latestStrategy = strategies[0] || null

  const handleGenerate = async () => {
    if (!publicKey || !amount) return

    setGenerating(true)
    try {
      await strategyApi.generateStrategy({
        wallet_address: publicKey.toBase58(),
        amount: parseFloat(amount),
        token: selectedToken,
        risk_level: riskLevel,
        duration: parseInt(duration),
        network,
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
        <div className="mb-8 grid gap-6 lg:grid-cols-[1.6fr_1fr] lg:items-start">
          <Card className="self-start overflow-hidden p-0">
            <div className="bg-[radial-gradient(circle_at_top_left,_rgba(99,102,241,0.35),_transparent_45%),linear-gradient(135deg,_rgba(17,24,39,0.98),_rgba(3,7,18,0.96))] p-8">
              <p className="text-sm uppercase tracking-[0.3em] text-indigo-300">Strategy Workspace</p>
              <h1 className="mt-3 text-3xl font-bold text-white">{t('strategy.title')}</h1>
              <p className="mt-3 max-w-2xl text-gray-300">
                AI 问答页负责帮你讨论、追问和生成策略，这里负责沉淀历史、查看详情和执行结果。
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link href="/ai">
                  <Button variant="primary" size="lg">
                    去 AI 助手生成策略
                  </Button>
                </Link>
                <Button variant="outline" size="lg" onClick={() => setShowQuickGenerator((prev) => !prev)}>
                  {showQuickGenerator ? '收起快速生成器' : '打开快速生成器'}
                </Button>
                <Button variant="ghost" size="lg" onClick={loadStrategies} disabled={!publicKey || loading}>
                  刷新策略记录
                </Button>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="text-lg font-semibold text-white">工作台概览</h2>
            <div className="mt-5 grid grid-cols-2 gap-4">
              <div className="rounded-2xl border border-gray-800 bg-gray-900/80 p-4">
                <p className="text-sm text-gray-400">总策略数</p>
                <p className="mt-2 text-3xl font-bold text-white">{strategies.length}</p>
              </div>
              <div className="rounded-2xl border border-gray-800 bg-gray-900/80 p-4">
                <p className="text-sm text-gray-400">活跃中</p>
                <p className="mt-2 text-3xl font-bold text-emerald-400">{activeStrategies.length}</p>
              </div>
              <div className="rounded-2xl border border-gray-800 bg-gray-900/80 p-4">
                <p className="text-sm text-gray-400">草案/待确认</p>
                <p className="mt-2 text-3xl font-bold text-yellow-400">{draftStrategies.length}</p>
              </div>
              <div className="rounded-2xl border border-gray-800 bg-gray-900/80 p-4">
                <p className="text-sm text-gray-400">当前网络</p>
                <p className="mt-2 text-lg font-bold uppercase text-indigo-300">{network}</p>
              </div>
            </div>
            <div className="mt-5 rounded-2xl border border-gray-800 bg-gray-900/60 p-4">
              <p className="text-sm text-gray-400">最近一条策略</p>
              <p className="mt-2 font-semibold text-white">
                {latestStrategy?.title || '还没有历史策略'}
              </p>
              <p className="mt-1 text-sm text-gray-500">
                {latestStrategy
                  ? `状态：${latestStrategy.status} · ${new Date(latestStrategy.created_at).toLocaleDateString('zh-CN')}`
                  : '先在 AI 助手里生成一版，再回到这里统一管理。'}
              </p>
            </div>
            {capabilities && (
              <div className="mt-5 rounded-2xl border border-indigo-500/20 bg-indigo-500/10 p-4">
                <p className="text-sm font-medium text-white">
                  {capabilities.demo_mode ? '当前为 DEMO 演示模式' : '当前为真实链路模式'}
                </p>
                <p className="mt-2 text-sm text-gray-300">
                  {capabilities.testing_guidance.best_demo_approach}
                </p>
              </div>
            )}
          </Card>
        </div>

        {showQuickGenerator && (
          <Card className="mb-8 p-6">
            <div className="mb-6 flex items-start justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-white">快速生成器</h2>
                <p className="mt-2 text-sm text-gray-400">
                  这是保留给你快速出一版草案的备用入口，更推荐在 AI 助手里边聊边改。
                </p>
              </div>
              <Link href="/ai" className="text-sm text-indigo-300 hover:text-indigo-200">
                去 AI 助手获得更可交互的结果
              </Link>
            </div>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div>
                <Input
                  label={t('strategy.amount')}
                  type="number"
                  placeholder="1000"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                />
              </div>

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
                {generating ? t('strategy.generating') || '生成中...' : '快速生成一版策略'}
              </Button>
              {!publicKey && <p className="mt-2 text-center text-sm text-yellow-500">请先连接钱包</p>}
            </div>
          </Card>
        )}

        <div className="mb-10">
          <div className="mb-6 flex items-end justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold text-white">活跃策略</h2>
              <p className="mt-2 text-gray-400">优先关注正在执行、已批准或最近需要你处理的策略。</p>
            </div>
            <Link href="/ai" className="text-sm text-indigo-300 hover:text-indigo-200">
              去 AI 助手继续优化
            </Link>
          </div>
          {loading ? (
            <div className="text-center text-gray-400">加载中...</div>
          ) : activeStrategies.length > 0 ? (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {activeStrategies.map((strategy) => (
                <StrategyCard key={strategy.id} {...convertStrategyToCardProps(strategy)} />
              ))}
            </div>
          ) : (
            <Card className="p-8 text-center">
              <p className="text-lg font-semibold text-white">
                {publicKey ? '当前没有活跃策略' : '请先连接钱包'}
              </p>
              <p className="mt-2 text-sm text-gray-400">
                {publicKey
                  ? '建议先去 AI 助手生成策略，再回到这里查看详情、执行和历史。'
                  : '连接钱包后即可查看属于你的策略历史。'}
              </p>
            </Card>
          )}
        </div>

        <div>
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-white">策略历史</h2>
            <p className="mt-2 text-gray-400">这里保留你生成过的草案、已执行方案和后续复盘入口。</p>
          </div>

          {loading ? null : draftStrategies.length > 0 ? (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {draftStrategies.map((strategy) => (
                <StrategyCard key={strategy.id} {...convertStrategyToCardProps(strategy)} />
              ))}
            </div>
          ) : (
            <Card className="p-8 text-center">
              <p className="text-lg font-semibold text-white">还没有历史草案</p>
              <p className="mt-2 text-sm text-gray-400">
                你在 AI 助手里生成的新策略、快速生成器产出的草案，都会沉淀到这里。
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
