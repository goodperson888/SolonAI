'use client'

export const dynamic = 'force-dynamic'

import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ArrowLeft, AlertTriangle, Clock, CheckCircle } from 'lucide-react'
import Link from 'next/link'
import { useWallet } from '@solana/wallet-adapter-react'
import { strategyApi, type Strategy } from '@/lib/api-client'

export default function StrategyDetailPage() {
  const params = useParams()
  const strategyId = params.id as string
  const { publicKey } = useWallet()
  const [strategy, setStrategy] = useState<Strategy | null>(null)
  const [loading, setLoading] = useState(true)
  const [executing, setExecuting] = useState(false)

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    loadStrategy()
  }, [strategyId])

  const loadStrategy = async () => {
    setLoading(true)
    try {
      const data = await strategyApi.getStrategy(strategyId)
      setStrategy(data.strategy)
    } catch (error) {
      console.error('Failed to load strategy:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleExecute = async () => {
    if (!publicKey || !strategy) return

    setExecuting(true)
    try {
      await strategyApi.executeStrategy(strategy.id, publicKey.toBase58())
      // 重新加载策略状态
      await loadStrategy()
    } catch (error) {
      console.error('Failed to execute strategy:', error)
    } finally {
      setExecuting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center text-gray-400">加载中...</div>
        </div>
      </div>
    )
  }

  if (!strategy) {
    return (
      <div className="min-h-screen bg-gray-950 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center text-gray-400">策略不存在</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-950 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* 返回按钮 */}
        <Link
          href="/strategy"
          className="mb-6 inline-flex items-center text-gray-400 transition-colors hover:text-white"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          返回策略列表
        </Link>

        {/* 策略概览 */}
        <Card className="mb-8 p-6">
          <div className="mb-6 flex items-start justify-between">
            <div>
              <h1 className="mb-2 text-3xl font-bold text-white">{strategy.goal}</h1>
              <p className="text-gray-400">{strategy.strategy_content}</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-green-400">
                {strategy.expected_return ? `${strategy.expected_return.toFixed(1)}%` : 'N/A'}
              </div>
              <div className="text-sm text-gray-400">预期年化收益</div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
            <div>
              <div className="mb-1 text-sm text-gray-400">风险等级</div>
              <div className="flex items-center">
                <span
                  className={`rounded-full px-3 py-1 text-sm ${
                    strategy.risk_level === 'conservative'
                      ? 'bg-green-500/20 text-green-400'
                      : strategy.risk_level === 'balanced'
                        ? 'bg-yellow-500/20 text-yellow-400'
                        : 'bg-red-500/20 text-red-400'
                  }`}
                >
                  {strategy.risk_tolerance}
                </span>
              </div>
            </div>
            <div>
              <div className="mb-1 text-sm text-gray-400">状态</div>
              <div className="text-lg font-semibold capitalize text-white">{strategy.status}</div>
            </div>
            <div>
              <div className="mb-1 text-sm text-gray-400">创建时间</div>
              <div className="text-lg font-semibold text-white">
                {new Date(strategy.created_at).toLocaleDateString('zh-CN')}
              </div>
            </div>
            <div>
              <div className="mb-1 text-sm text-gray-400">时间范围</div>
              <div className="text-lg font-semibold text-white">{strategy.time_horizon}</div>
            </div>
          </div>
        </Card>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* 左侧：策略详情 */}
          <div className="space-y-8 lg:col-span-2">
            {/* 执行步骤 */}
            <Card className="p-6">
              <h2 className="mb-6 text-xl font-bold text-white">推荐操作</h2>
              <div className="space-y-4">
                {strategy.recommended_actions.map((action, index) => (
                  <div key={index} className="flex items-start">
                    <div className="mr-4 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-indigo-600 font-semibold text-white">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <h3 className="mb-1 font-semibold text-white">{action.action}</h3>
                      <p className="text-sm text-gray-400">{action.reason}</p>
                      {action.token && (
                        <div className="mt-2 text-xs text-gray-500">
                          代币: {action.token} {action.amount && `| 数量: ${action.amount}`}
                        </div>
                      )}
                    </div>
                    {strategy.status === 'executed' || strategy.status === 'completed' ? (
                      <CheckCircle className="h-5 w-5 text-green-400" />
                    ) : (
                      <div className="h-5 w-5 rounded-full border-2 border-gray-600" />
                    )}
                  </div>
                ))}
              </div>

              <div className="mt-6 border-t border-gray-800 pt-6">
                <Button
                  variant="primary"
                  size="lg"
                  className="w-full"
                  onClick={handleExecute}
                  disabled={
                    !publicKey ||
                    executing ||
                    strategy.status === 'executed' ||
                    strategy.status === 'completed'
                  }
                >
                  {executing
                    ? '执行中...'
                    : strategy.status === 'executed' || strategy.status === 'completed'
                      ? '已执行'
                      : '一键执行策略'}
                </Button>
                {!publicKey && (
                  <p className="mt-2 text-center text-sm text-yellow-500">请先连接钱包</p>
                )}
              </div>
            </Card>

            {/* 策略内容 */}
            <Card className="p-6">
              <h2 className="mb-6 text-xl font-bold text-white">策略详情</h2>
              <div className="prose prose-invert max-w-none">
                <p className="whitespace-pre-wrap text-gray-300">{strategy.strategy_content}</p>
              </div>
            </Card>

            {/* 风险提示 */}
            <Card className="p-6">
              <h2 className="mb-6 text-xl font-bold text-white">风险提示</h2>
              <div className="space-y-4">
                <div className="flex items-start rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-4">
                  <AlertTriangle className="mr-3 mt-0.5 h-5 w-5 flex-shrink-0 text-yellow-400" />
                  <div>
                    <h3 className="mb-1 font-semibold text-yellow-400">市场风险</h3>
                    <p className="text-sm text-gray-300">
                      加密货币市场波动较大，请根据自身风险承受能力谨慎投资。
                    </p>
                  </div>
                </div>

                <div className="flex items-start rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-4">
                  <AlertTriangle className="mr-3 mt-0.5 h-5 w-5 flex-shrink-0 text-yellow-400" />
                  <div>
                    <h3 className="mb-1 font-semibold text-yellow-400">智能合约风险</h3>
                    <p className="text-sm text-gray-300">
                      DeFi 协议存在智能合约漏洞风险，建议分散投资。
                    </p>
                  </div>
                </div>

                <div className="flex items-start rounded-lg border border-blue-500/30 bg-blue-500/10 p-4">
                  <Clock className="mr-3 mt-0.5 h-5 w-5 flex-shrink-0 text-blue-400" />
                  <div>
                    <h3 className="mb-1 font-semibold text-blue-400">投资建议</h3>
                    <p className="text-sm text-gray-300">
                      建议长期持有以获得更好的收益，频繁交易会增加成本。
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* 右侧：监控面板 */}
          <div className="space-y-8">
            {/* 策略信息 */}
            <Card className="p-6">
              <h2 className="mb-4 text-lg font-bold text-white">策略信息</h2>
              <div className="space-y-4">
                <div>
                  <div className="mb-1 text-sm text-gray-400">风险等级</div>
                  <div className="text-xl font-bold capitalize text-white">
                    {strategy.risk_level}
                  </div>
                </div>
                <div>
                  <div className="mb-1 text-sm text-gray-400">预期收益</div>
                  <div className="text-xl font-bold text-green-400">
                    {strategy.expected_return ? `${strategy.expected_return.toFixed(1)}%` : 'N/A'}
                  </div>
                </div>
                <div>
                  <div className="mb-1 text-sm text-gray-400">状态</div>
                  <div
                    className={`text-xl font-bold capitalize ${
                      strategy.status === 'completed'
                        ? 'text-green-400'
                        : strategy.status === 'executed'
                          ? 'text-blue-400'
                          : strategy.status === 'active'
                            ? 'text-yellow-400'
                            : 'text-gray-400'
                    }`}
                  >
                    {strategy.status}
                  </div>
                </div>
              </div>
            </Card>

            {/* 时间信息 */}
            <Card className="p-6">
              <h2 className="mb-4 text-lg font-bold text-white">时间信息</h2>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">创建时间</span>
                  <span className="text-sm font-semibold text-white">
                    {new Date(strategy.created_at).toLocaleString('zh-CN')}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">时间范围</span>
                  <span className="text-sm text-white">{strategy.time_horizon}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">风险承受度</span>
                  <span className="text-sm capitalize text-white">{strategy.risk_tolerance}</span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
