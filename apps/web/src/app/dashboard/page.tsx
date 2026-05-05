'use client'

import { useState, useEffect } from 'react'
import { useWallet } from '@solana/wallet-adapter-react'
import { StatCard } from '@/components/dashboard/StatCard'
import { AssetCard } from '@/components/assets/AssetCard'
import { StrategyCard } from '@/components/strategy/StrategyCard'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { useTranslation } from '@/hooks/useTranslation'
import {
  assetsApi,
  strategyApi,
  WalletAssetsResponse,
  AssetDiagnosisResponse,
  PnLResponse,
  Strategy,
  StrategyCapabilitiesResponse,
} from '@/lib/api-client'
import { useSolanaNetwork } from '@/components/wallet/NetworkContext'

type TabType = 'overview' | 'profit' | 'risk'

export default function DashboardPage() {
  const { t } = useTranslation()
  const { publicKey, connected } = useWallet()
  const { network } = useSolanaNetwork()
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [walletAssets, setWalletAssets] = useState<WalletAssetsResponse | null>(null)
  const [diagnosis, setDiagnosis] = useState<AssetDiagnosisResponse | null>(null)
  const [pnl, setPnl] = useState<PnLResponse | null>(null)
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [capabilities, setCapabilities] = useState<StrategyCapabilitiesResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 获取钱包资产
  const fetchWalletAssets = async () => {
    if (!publicKey) return

    setIsLoading(true)
    setError(null)
    try {
      const data = await assetsApi.getWalletAssets(publicKey.toBase58(), network)
      setWalletAssets(data)
    } catch (err) {
      console.error('Failed to fetch wallet assets:', err)
      setError('获取资产数据失败')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (connected && publicKey) {
      fetchWalletAssets()
      fetchStrategies()
      fetchPnL()
      if (activeTab === 'risk') {
        fetchDiagnosis()
      }
    } else {
      setWalletAssets(null)
      setDiagnosis(null)
      setPnl(null)
      setStrategies([])
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [connected, publicKey, activeTab, network])

  const fetchPnL = async () => {
    if (!publicKey) return

    setIsLoading(true)
    try {
      const data = await assetsApi.getPnL(publicKey.toBase58(), network)
      setPnl(data)
    } catch (err) {
      console.error('Failed to fetch PnL:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchDiagnosis = async () => {
    if (!publicKey) return

    setIsLoading(true)
    try {
      const data = await assetsApi.getDiagnosis(publicKey.toBase58(), network)
      setDiagnosis(data)
    } catch (err) {
      console.error('Failed to fetch diagnosis:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchStrategies = async () => {
    if (!publicKey) return

    try {
      const data = await strategyApi.listStrategies(publicKey.toBase58())
      setStrategies(data.strategies || [])
    } catch (err) {
      console.error('Failed to fetch strategies:', err)
    }
  }

  useEffect(() => {
    strategyApi
      .getCapabilities()
      .then(setCapabilities)
      .catch((err) => console.error('Failed to load capabilities:', err))
  }, [])

  const getExecutionPresentation = (strategy: Strategy) => {
    const protocolKey = (strategy.protocol_name || '').toLowerCase()
    const capability = capabilities?.protocols?.[protocolKey]
    const realExecutable =
      capability?.wallet_signature && network === 'mainnet' && !capabilities?.demo_mode

    let executionLabel = '查看执行详情'
    let executionHint = '进入详情页查看当前策略的执行结果与下一步动作。'

    if (capabilities?.demo_mode) {
      executionLabel = '查看演示预览'
      executionHint = '当前为 DEMO 演示模式，执行页会展示完整预览闭环。'
    } else if (realExecutable) {
      executionLabel = '尝试拉起钱包'
      executionHint = '当前协议支持主网签名链路，可在详情页尝试生成待签名交易。'
    } else if (network === 'devnet') {
      executionLabel = '查看开发网预览'
      executionHint = '开发网下默认展示参数预览、风控提示与费用估计。'
    } else if (capability?.notes) {
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

  const convertStrategyToCardProps = (strategy: Strategy) => ({
    id: strategy.id,
    name: strategy.title || '投资策略',
    protocol: strategy.protocol_name || 'DeFi Protocol',
    expectedAPY: strategy.estimated_apy || 0,
    riskLevel: strategy.risk_level === 'conservative' ? 'low' as const :
               strategy.risk_level === 'balanced' ? 'medium' as const : 'high' as const,
    lockPeriod: '灵活',
    steps: strategy.steps?.map(s => s.description) || [],
    deployed: strategy.status === 'approved' || strategy.status === 'executed',
    deployedAmount: strategy.input_amount || 0,
    detailsHref: `/strategy/${strategy.id}`,
    actionHref: `/strategy/${strategy.id}`,
    ...getExecutionPresentation(strategy),
  })

  type DisplayAsset = {
    id: string
    icon: string
    symbol: string
    name: string
    amount: number
    value: number
    change24h: number
  }

  const displayAssets: DisplayAsset[] = walletAssets
    ? [
        {
          id: 'sol',
          icon: 'S',
          symbol: 'SOL',
          name: 'Solana',
          amount: walletAssets.sol_balance,
          value: walletAssets.sol_value_usd,
          change24h: 0,
        },
        ...walletAssets.tokens.map((token) => ({
          id: token.mint,
          icon: token.symbol.charAt(0),
          symbol: token.symbol,
          name: token.name,
          amount: token.balance,
          value: token.usd_value,
          change24h: 0,
        })),
      ]
    : []

  const totalValue = walletAssets?.total_value_usd || 0

  const tabs = [
    { id: 'overview' as TabType, name: '资产总览' },
    { id: 'profit' as TabType, name: '盈亏分析' },
    { id: 'risk' as TabType, name: '风险诊断' },
  ]

  return (
    <div className="min-h-screen bg-gray-950 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Page Title */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">{t('dashboard.title')}</h1>
          <p className="mt-2 text-gray-400">
            {connected
              ? `钱包已连接: ${publicKey?.toBase58().slice(0, 8)}...`
              : '欢迎回来！这是你的资产概览'}
          </p>
        </div>

        {/* 钱包未连接提示 */}
        {!connected && (
          <Card className="mb-8 p-6">
            <div className="flex items-center gap-4">
              <span className="text-4xl">👛</span>
              <div className="flex-1">
                <h3 className="mb-2 text-lg font-semibold text-white">连接钱包查看真实资产</h3>
                <p className="text-sm text-gray-400">
                  点击右上角连接钱包按钮，即可查看您的链上资产数据
                </p>
              </div>
            </div>
          </Card>
        )}

        {/* 加载状态 */}
        {isLoading && (
          <Card className="mb-8 p-6">
            <div className="flex items-center gap-4">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
              <p className="text-gray-400">正在加载链上资产数据...</p>
            </div>
          </Card>
        )}

        {/* 错误提示 */}
        {error && (
          <Card className="mb-8 border border-red-500/30 bg-red-500/10 p-6">
            <div className="flex items-center gap-4">
              <span className="text-2xl">⚠️</span>
              <div className="flex-1">
                <h3 className="mb-1 font-semibold text-white">加载失败</h3>
                <p className="text-sm text-gray-300">{error}</p>
              </div>
              <Button variant="outline" size="sm" onClick={fetchWalletAssets}>
                重试
              </Button>
            </div>
          </Card>
        )}

        {connected && walletAssets?.network_hint && (
          <Card className="mb-8 border border-yellow-500/30 bg-yellow-500/10 p-6">
            <div className="flex items-start gap-4">
              <span className="text-2xl">🌐</span>
              <div className="flex-1">
                <h3 className="mb-1 font-semibold text-white">检测到网络不一致</h3>
                <p className="text-sm text-gray-300">{walletAssets.network_hint}</p>
                <p className="mt-2 text-xs text-gray-400">
                  如果你想查看这笔资产，请用 devnet 启动后端，或把钱包切换到主网资产地址。
                </p>
              </div>
            </div>
          </Card>
        )}

        {/* Stats Cards */}
        <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title={t('dashboard.totalValue')}
            value={`$${totalValue.toLocaleString()}`}
            change={pnl ? pnl.total_pnl_percentage : 0}
            trend={pnl && pnl.total_pnl >= 0 ? 'up' : 'down'}
            icon="💰"
          />
          <StatCard
            title={t('dashboard.todayProfit')}
            value={pnl ? `${pnl.total_pnl >= 0 ? '+' : ''}$${pnl.total_pnl.toFixed(2)}` : '$0.00'}
            change={pnl ? pnl.roi_percentage : 0}
            trend={pnl && pnl.total_pnl >= 0 ? 'up' : 'down'}
            icon="📈"
          />
          <StatCard
            title={t('dashboard.activeStrategies')}
            value={strategies.filter((s: Strategy) => s.status === 'approved' || s.status === 'executed').length}
            icon="⚡"
          />
          <StatCard title={t('dashboard.riskLevel')} value={diagnosis?.risk_level || t('common.low')} icon="🛡️" />
        </div>

        {/* Tabs */}
        <div className="mb-8">
          <div className="border-b border-gray-800">
            <nav className="flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`border-b-2 px-1 py-4 text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-400'
                      : 'border-transparent text-gray-400 hover:border-gray-700 hover:text-gray-300'
                  }`}
                >
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Assets Section */}
            <div>
              <div className="mb-6 flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white">{t('dashboard.assets')}</h2>
                <button className="text-sm text-indigo-400 hover:text-indigo-300">
                  查看全部 →
                </button>
              </div>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
                {displayAssets.map((asset) => (
                  <AssetCard key={asset.id} {...asset} />
                ))}
              </div>

              {connected &&
                walletAssets &&
                walletAssets.tokens.length === 0 &&
                walletAssets.sol_balance === 0 && (
                  <Card className="p-6">
                    <div className="text-center">
                      <span className="text-4xl">🪙</span>
                      <h3 className="mt-4 text-lg font-semibold text-white">钱包暂无资产</h3>
                      <p className="mt-2 text-sm text-gray-400">您的钱包中还没有任何资产</p>
                    </div>
                  </Card>
                )}
            </div>

            {/* Active Strategies Section */}
            <div>
              <div className="mb-6 flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white">活跃策略</h2>
                <button className="text-sm text-indigo-400 hover:text-indigo-300">
                  查看全部 →
                </button>
              </div>
              {connected && strategies.length > 0 ? (
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {strategies
                    .filter((s) => s.status === 'approved' || s.status === 'executed')
                    .slice(0, 3)
                    .map((strategy) => (
                      <StrategyCard key={strategy.id} {...convertStrategyToCardProps(strategy)} />
                    ))}
                </div>
              ) : connected ? (
                <Card className="p-6">
                  <div className="text-center">
                    <span className="text-4xl">📊</span>
                    <h3 className="mt-4 text-lg font-semibold text-white">暂无活跃策略</h3>
                    <p className="mt-2 text-sm text-gray-400">前往策略中心生成您的第一个策略</p>
                  </div>
                </Card>
              ) : (
                <Card className="p-6">
                  <div className="text-center">
                    <span className="text-4xl">📊</span>
                    <h3 className="mt-4 text-lg font-semibold text-white">暂无活跃策略</h3>
                    <p className="mt-2 text-sm text-gray-400">请先连接钱包，然后前往策略中心生成策略</p>
                  </div>
                </Card>
              )}
            </div>
          </div>
        )}

        {activeTab === 'profit' && (
          <div className="space-y-8">
            {/* 盈亏概览 */}
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
              <Card className="p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white">总盈亏</h3>
                  <span className="text-2xl">📊</span>
                </div>
                <p
                  className={`mb-2 text-3xl font-bold ${
                    pnl && pnl.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {pnl ? `${pnl.total_pnl >= 0 ? '+' : ''}$${pnl.total_pnl.toFixed(2)}` : '+$0.00'}
                </p>
                <p className="text-sm text-gray-400">
                  年化收益率: {pnl ? `${pnl.roi_percentage.toFixed(1)}%` : 'N/A'}
                </p>
              </Card>

              <Card className="p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white">持仓盈亏</h3>
                  <span className="text-2xl">💎</span>
                </div>
                <p
                  className={`mb-2 text-3xl font-bold ${
                    pnl && pnl.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {pnl
                    ? `${pnl.unrealized_pnl >= 0 ? '+' : ''}$${pnl.unrealized_pnl.toFixed(2)}`
                    : '+$0.00'}
                </p>
                <p className="text-sm text-gray-400">浮动盈亏</p>
              </Card>

              <Card className="p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white">已实现盈亏</h3>
                  <span className="text-2xl">🌾</span>
                </div>
                <p
                  className={`mb-2 text-3xl font-bold ${
                    pnl && pnl.realized_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {pnl
                    ? `${pnl.realized_pnl >= 0 ? '+' : ''}$${pnl.realized_pnl.toFixed(2)}`
                    : '+$0.00'}
                </p>
                <p className="text-sm text-gray-400">历史交易</p>
              </Card>
            </div>

            {/* 详细盈亏分析 */}
            {pnl && pnl.breakdown && pnl.breakdown.length > 0 && (
              <Card className="p-6">
                <h2 className="mb-6 text-xl font-bold text-white">盈亏明细</h2>
                <div className="space-y-4">
                  {pnl.breakdown.map((item, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between rounded-lg bg-gray-800 p-4"
                    >
                      <div>
                        <p className="font-medium text-white">{item.asset}</p>
                        <p className="mt-1 text-sm text-gray-400">{item.type}</p>
                      </div>
                      <div className="text-right">
                        <p
                          className={`text-xl font-bold ${
                            item.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}
                        >
                          {item.pnl >= 0 ? '+' : ''}${item.pnl.toFixed(2)}
                        </p>
                        <p className="text-sm text-gray-400">
                          {item.percentage >= 0 ? '+' : ''}
                          {item.percentage.toFixed(2)}%
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {!pnl && !isLoading && (
              <Card className="p-6">
                <div className="text-center text-gray-400">暂无盈亏数据</div>
              </Card>
            )}
          </div>
        )}

        {activeTab === 'risk' && (
          <div className="space-y-8">
            {/* 风险概览 */}
            <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
              <Card className="p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-400">风险评分</h3>
                  <span className="text-2xl">🔍</span>
                </div>
                <p
                  className={`text-3xl font-bold ${
                    diagnosis?.risk_level === 'low'
                      ? 'text-green-400'
                      : diagnosis?.risk_level === 'medium'
                        ? 'text-yellow-400'
                        : 'text-red-400'
                  }`}
                >
                  {diagnosis?.risk_score || 'N/A'}
                </p>
              </Card>

              <Card className="p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-400">风险等级</h3>
                  <span className="text-2xl">⚠️</span>
                </div>
                <p
                  className={`text-2xl font-bold capitalize ${
                    diagnosis?.risk_level === 'low'
                      ? 'text-green-400'
                      : diagnosis?.risk_level === 'medium'
                        ? 'text-yellow-400'
                        : 'text-red-400'
                  }`}
                >
                  {diagnosis?.risk_level || 'N/A'}
                </p>
              </Card>

              <Card className="p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-400">风险项</h3>
                  <span className="text-2xl">⚡</span>
                </div>
                <p className="text-3xl font-bold text-yellow-400">
                  {diagnosis?.issues.length || 0}
                </p>
              </Card>

              <Card className="p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-400">健康度</h3>
                  <span className="text-2xl">ℹ️</span>
                </div>
                <p className="text-3xl font-bold text-blue-400">
                  {diagnosis?.health_metrics.diversification_score || 'N/A'}
                </p>
              </Card>
            </div>

            {/* 风险诊断 */}
            <Card className="p-6">
              <h2 className="mb-6 text-xl font-bold text-white">风险诊断</h2>
              <div className="space-y-4">
                {diagnosis && diagnosis.issues.length > 0 ? (
                  diagnosis.issues.map((issue, index) => (
                    <div
                      key={index}
                      className={`rounded-lg border p-4 ${
                        issue.severity === 'high' || issue.severity === 'critical'
                          ? 'border-red-500/30 bg-red-500/10'
                          : issue.severity === 'medium'
                            ? 'border-yellow-500/30 bg-yellow-500/10'
                            : 'border-green-500/30 bg-green-500/10'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">
                          {issue.severity === 'high' || issue.severity === 'critical'
                            ? '⚠️'
                            : issue.severity === 'medium'
                              ? '⚡'
                              : '✅'}
                        </span>
                        <div className="flex-1">
                          <div className="mb-2 flex items-center justify-between">
                            <h3 className="font-semibold text-white">{issue.type}</h3>
                            <span
                              className={`rounded px-2 py-1 text-xs text-white ${
                                issue.severity === 'high' || issue.severity === 'critical'
                                  ? 'bg-red-500'
                                  : issue.severity === 'medium'
                                    ? 'bg-yellow-500'
                                    : 'bg-green-500'
                              }`}
                            >
                              {issue.severity}
                            </span>
                          </div>
                          <p className="mb-3 text-sm text-gray-300">{issue.description}</p>
                          <p className="text-sm text-gray-400">建议: {issue.recommendation}</p>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="rounded-lg border border-green-500/30 bg-green-500/10 p-4">
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">✅</span>
                      <div className="flex-1">
                        <h3 className="mb-2 font-semibold text-white">资产安全</h3>
                        <p className="text-sm text-gray-300">
                          {diagnosis ? '您的资产状态良好，未发现明显风险' : '暂无诊断数据'}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </Card>

            {/* 健康指标 */}
            {diagnosis?.health_metrics && (
              <Card className="p-6">
                <h2 className="mb-6 text-xl font-bold text-white">健康指标</h2>
                <div className="space-y-4">
                  <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
                    <div>
                      <p className="font-medium text-white">多样化评分</p>
                      <p className="mt-1 text-sm text-gray-400">资产分散程度</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xl font-bold text-white">
                        {diagnosis.health_metrics.diversification_score}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
                    <div>
                      <p className="font-medium text-white">流动性评分</p>
                      <p className="mt-1 text-sm text-gray-400">资产变现能力</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xl font-bold text-white">
                        {diagnosis.health_metrics.liquidity_score}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
                    <div>
                      <p className="font-medium text-white">波动性评分</p>
                      <p className="mt-1 text-sm text-gray-400">价格稳定性</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xl font-bold text-white">
                        {diagnosis.health_metrics.volatility_score}
                      </p>
                    </div>
                  </div>
                </div>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
