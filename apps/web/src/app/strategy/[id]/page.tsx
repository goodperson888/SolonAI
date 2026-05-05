'use client'

export const dynamic = 'force-dynamic'

import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ArrowLeft, AlertTriangle, CheckCircle, Clock } from 'lucide-react'
import Link from 'next/link'
import { useConnection, useWallet } from '@solana/wallet-adapter-react'
import { VersionedTransaction } from '@solana/web3.js'
import {
  strategyApi,
  type Strategy,
  type StrategyCapabilitiesResponse,
  type TransactionResponse,
} from '@/lib/api-client'
import { useSolanaNetwork } from '@/components/wallet/NetworkContext'

const riskLevelLabel: Record<string, string> = {
  conservative: '保守',
  balanced: '稳健',
  aggressive: '激进',
}

const statusColor: Record<string, string> = {
  generated: 'text-gray-400',
  approved: 'text-yellow-400',
  prepared: 'text-blue-400',
  executing: 'text-blue-400',
  executed: 'text-green-400',
  completed: 'text-green-400',
  expired: 'text-red-400',
}

function resolveExecutionPresentation(params: {
  strategy: Strategy
  capabilities: StrategyCapabilitiesResponse | null
  network: 'mainnet' | 'devnet'
  executionMode: 'auto' | 'simulate' | 'build'
}) {
  const { strategy, capabilities, network, executionMode } = params
  const protocolKey = (strategy.protocol_name || '').toLowerCase()
  const protocolCapability = capabilities?.protocols?.[protocolKey]
  const demoMode = Boolean(capabilities?.demo_mode)
  const walletSignatureSupported = Boolean(protocolCapability?.wallet_signature)
  const isMainnetSignable =
    !demoMode && network === 'mainnet' && walletSignatureSupported

  let buttonLabel = '生成执行结果'
  let helperText = '先生成一份执行结果，查看费用估计、协议参数和下一步动作。'
  let badge = '执行预览'

  if (executionMode === 'simulate') {
    buttonLabel = '生成模拟结果'
    helperText = '当前会直接生成模拟结果，不会拉起钱包签名。'
    badge = '模拟模式'
  } else if (executionMode === 'build') {
    buttonLabel = isMainnetSignable ? '生成待签名交易' : '生成预构建结果'
    helperText = isMainnetSignable
      ? '当前会优先生成待签名交易，成功后可继续拉起钱包。'
      : '当前会先生成预构建结果，展示协议参数和下一步提示。'
    badge = '预构建模式'
  } else if (demoMode) {
    buttonLabel = '生成演示结果'
    helperText = '当前为 DEMO 演示模式，适合完整演示流程，但不会发起真实签名。'
    badge = 'DEMO 模式'
  } else if (network === 'devnet') {
    buttonLabel = '生成开发网预览'
    helperText = '当前网络为 devnet，默认先展示执行预览和风控确认。'
    badge = '开发网预览'
  } else if (isMainnetSignable) {
    buttonLabel = '生成并尝试拉起钱包'
    helperText = '当前协议支持主网签名链路，生成成功后会尝试拉起钱包。'
    badge = '可签名执行'
  } else if (protocolCapability?.notes) {
    buttonLabel = '生成参数预览'
    helperText = protocolCapability.notes
    badge = '参数预览'
  }

  return {
    buttonLabel,
    helperText,
    badge,
    protocolCapability,
    isMainnetSignable,
  }
}

export default function StrategyDetailPage() {
  const params = useParams()
  const strategyId = params.id as string
  const { publicKey, sendTransaction, connected } = useWallet()
  const { connection } = useConnection()
  const { network } = useSolanaNetwork()
  const [strategy, setStrategy] = useState<Strategy | null>(null)
  const [transaction, setTransaction] = useState<TransactionResponse | null>(null)
  const [capabilities, setCapabilities] = useState<StrategyCapabilitiesResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [executing, setExecuting] = useState(false)
  const [executionMode, setExecutionMode] = useState<'auto' | 'simulate' | 'build'>('auto')
  const [submitMessage, setSubmitMessage] = useState('')

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    loadStrategy()
    loadCapabilities()
  }, [strategyId])

  const loadStrategy = async (showLoading = true) => {
    if (showLoading) {
      setLoading(true)
    }
    try {
      const data = await strategyApi.getStrategy(strategyId)
      setStrategy(data)
    } catch (error) {
      console.error('Failed to load strategy:', error)
    } finally {
      if (showLoading) {
        setLoading(false)
      }
    }
  }

  const loadCapabilities = async () => {
    try {
      const data = await strategyApi.getCapabilities()
      setCapabilities(data)
    } catch (error) {
      console.error('Failed to load strategy capabilities:', error)
    }
  }

  const handleExecute = async () => {
    if (!publicKey || !strategy) return

    setExecuting(true)
    setSubmitMessage('')
    try {
      const tx = await strategyApi.executeStrategy(
        strategy.id,
        publicKey.toBase58(),
        network,
        executionMode
      )

      const serializedTx = tx.tx_payload?.swap_transaction_base64
      if (typeof serializedTx === 'string' && executionMode !== 'simulate' && connected) {
        const raw = Uint8Array.from(atob(serializedTx), (char) => char.charCodeAt(0))
        const versionedTx = VersionedTransaction.deserialize(raw)
        const signature = await sendTransaction(versionedTx, connection)
        await connection.confirmTransaction(signature, 'confirmed')

        const completed = await strategyApi.completePreparedTransaction(tx.id, signature, 'confirmed')
        setTransaction(completed)
        setSubmitMessage(`钱包已签名并提交交易: ${signature.slice(0, 12)}...`)
      } else {
        setTransaction(tx)
        if (executionMode === 'simulate' || tx.tx_payload?.simulation_only) {
          setSubmitMessage('当前为模拟/预览模式，因此不会拉起钱包签名。')
        } else if (!serializedTx) {
          setSubmitMessage('当前策略暂未生成可签名交易，先展示参数预览和执行提示。')
        }
      }

      await loadStrategy(false)
    } catch (error) {
      console.error('Failed to execute strategy:', error)
      setSubmitMessage('执行失败：可能是钱包未授权、交易构建失败，或当前策略还不支持直接签名。')
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

  const displayRisk = riskLevelLabel[strategy.risk_level] || strategy.risk_level
  const canExecute = !['executed', 'completed'].includes(strategy.status)
  const warnings = strategy.risk_assessment?.warnings || []
  const checks = strategy.risk_assessment?.checks || []
  const simulation = transaction?.simulation_result || {}
  const txPayload = transaction?.tx_payload || {}
  const simulationNote = typeof simulation.note === 'string' ? simulation.note : ''
  const simulationNetworkHint =
    typeof simulation.network_hint === 'string' ? simulation.network_hint : ''
  const simulationError = typeof simulation.error === 'string' ? simulation.error : ''
  const nextStepHint = typeof txPayload.next_step === 'string' ? txPayload.next_step : ''
  const simulationMode = typeof simulation.mode === 'string' ? simulation.mode : ''
  const estimatedFee =
    typeof simulation.estimated_fee_sol === 'number' ? simulation.estimated_fee_sol : null
  const previewPayload =
    simulation.preview_payload && typeof simulation.preview_payload === 'object'
      ? (simulation.preview_payload as {
          headline?: string
          summary?: string
          steps?: string[]
        })
      : txPayload.preview_payload && typeof txPayload.preview_payload === 'object'
        ? (txPayload.preview_payload as {
            headline?: string
            summary?: string
            steps?: string[]
          })
        : null
  const executionBadge = txPayload.simulation_only
    ? capabilities?.demo_mode
      ? '演示模式'
      : network === 'devnet'
        ? '开发网预览'
        : '预览模式'
    : '可签名执行'
  const executionPresentation = resolveExecutionPresentation({
    strategy,
    capabilities,
    network,
    executionMode,
  })
  const protocolCapability = executionPresentation.protocolCapability

  return (
    <div className="min-h-screen bg-gray-950 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Link
          href="/strategy"
          className="mb-6 inline-flex items-center text-gray-400 transition-colors hover:text-white"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          返回策略工作台
        </Link>

        {capabilities && (
          <Card className="mb-6 border border-indigo-500/30 bg-indigo-500/10 p-4">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-indigo-500/20 px-2.5 py-1 text-xs font-medium text-indigo-200">
                    {capabilities.demo_mode ? 'DEMO 演示模式' : '真实链路模式'}
                  </span>
                  <span className="rounded-full bg-gray-900/70 px-2.5 py-1 text-xs font-medium text-gray-300">
                    {executionBadge}
                  </span>
                </div>
                <p className="text-sm text-gray-200">
                  {protocolCapability?.notes ||
                    '当前页面会根据协议能力决定是直接拉起钱包，还是先展示最接近真实的参数预览。'}
                </p>
              </div>
              <div className="max-w-xl text-xs text-gray-300">
                {capabilities.testing_guidance.best_demo_approach}
              </div>
            </div>
          </Card>
        )}

        <Card className="mb-8 p-6">
          <div className="mb-6 flex items-start justify-between gap-6">
            <div>
              <h1 className="mb-2 text-3xl font-bold text-white">{strategy.title}</h1>
              <p className="text-gray-400">{strategy.summary || 'AI 已为你生成一套可执行的 DeFi 策略。'}</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-green-400">
                {strategy.estimated_apy ? `${strategy.estimated_apy.toFixed(1)}%` : 'N/A'}
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
                  {displayRisk}
                </span>
              </div>
            </div>
            <div>
              <div className="mb-1 text-sm text-gray-400">协议</div>
              <div className="text-lg font-semibold text-white">{strategy.protocol_name || '待定'}</div>
            </div>
            <div>
              <div className="mb-1 text-sm text-gray-400">投入资产</div>
              <div className="text-lg font-semibold text-white">
                {strategy.input_amount ? `${strategy.input_amount} ${strategy.input_token}` : strategy.input_token}
              </div>
            </div>
            <div>
              <div className="mb-1 text-sm text-gray-400">创建时间</div>
              <div className="text-lg font-semibold text-white">
                {new Date(strategy.created_at).toLocaleDateString('zh-CN')}
              </div>
            </div>
          </div>
        </Card>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          <div className="space-y-8 lg:col-span-2">
            <Card className="p-6">
              <h2 className="mb-6 text-xl font-bold text-white">执行步骤</h2>
              <div className="space-y-4">
                {strategy.steps?.length ? (
                  strategy.steps.map((step, index) => (
                    <div key={`${step.protocol}-${index}`} className="flex items-start">
                      <div className="mr-4 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-indigo-600 font-semibold text-white">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <h3 className="mb-1 font-semibold text-white">{step.action}</h3>
                        <p className="text-sm text-gray-400">{step.description}</p>
                        <div className="mt-2 text-xs text-gray-500">
                          协议: {step.protocol} | 代币: {step.token} | 数量: {step.amount}
                        </div>
                      </div>
                      {strategy.status === 'executed' || strategy.status === 'completed' ? (
                        <CheckCircle className="h-5 w-5 text-green-400" />
                      ) : (
                        <div className="h-5 w-5 rounded-full border-2 border-gray-600" />
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-gray-400">暂无可展示的执行步骤</p>
                )}
              </div>

              <div className="mt-6 border-t border-gray-800 pt-6">
                <Button
                  variant="primary"
                  size="lg"
                  className="w-full"
                  onClick={handleExecute}
                  disabled={!publicKey || executing || !canExecute}
                >
                  {executing ? '处理中...' : !canExecute ? '已执行' : executionPresentation.buttonLabel}
                </Button>
                <div className="mt-4 grid grid-cols-3 gap-2">
                  {[
                    { value: 'auto', label: '自动' },
                    { value: 'simulate', label: '模拟' },
                    { value: 'build', label: '预构建' },
                  ].map((mode) => (
                    <button
                      key={mode.value}
                      onClick={() => setExecutionMode(mode.value as 'auto' | 'simulate' | 'build')}
                      className={`rounded-lg border px-3 py-2 text-sm transition-colors ${
                        executionMode === mode.value
                          ? 'border-indigo-500 bg-indigo-500/15 text-indigo-300'
                          : 'border-gray-700 bg-gray-900 text-gray-400 hover:border-gray-600'
                      }`}
                    >
                      {mode.label}
                    </button>
                  ))}
                </div>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-indigo-500/15 px-2.5 py-1 text-xs text-indigo-200">
                    {executionPresentation.badge}
                  </span>
                  <span className="text-xs text-gray-500">
                    当前网络: {network}。devnet 下默认走模拟；mainnet 下可尝试生成真实待签名交易。
                  </span>
                </div>
                <p className="mt-2 text-xs text-gray-400">
                  {executionPresentation.helperText}
                </p>
                {submitMessage && <p className="mt-3 rounded-lg border border-indigo-500/20 bg-indigo-500/10 px-3 py-2 text-center text-sm text-indigo-300">{submitMessage}</p>}
                {!publicKey && (
                  <p className="mt-2 text-center text-sm text-yellow-500">请先连接钱包</p>
                )}
              </div>
            </Card>

            <Card className="p-6">
              <h2 className="mb-6 text-xl font-bold text-white">策略说明</h2>
              <div className="prose prose-invert max-w-none">
                <p className="whitespace-pre-wrap text-gray-300">
                  {strategy.summary || '当前策略暂无额外说明。'}
                </p>
              </div>
            </Card>

            <Card className="p-6">
              <h2 className="mb-6 text-xl font-bold text-white">风险提示</h2>
              <div className="space-y-4">
                {warnings.length ? (
                  warnings.map((warning, index) => (
                    <div
                      key={`${warning}-${index}`}
                      className="flex items-start rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-4"
                    >
                      <AlertTriangle className="mr-3 mt-0.5 h-5 w-5 flex-shrink-0 text-yellow-400" />
                      <div>
                        <h3 className="mb-1 font-semibold text-yellow-400">风险提醒</h3>
                        <p className="text-sm text-gray-300">{warning}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="flex items-start rounded-lg border border-blue-500/30 bg-blue-500/10 p-4">
                    <Clock className="mr-3 mt-0.5 h-5 w-5 flex-shrink-0 text-blue-400" />
                    <div>
                      <h3 className="mb-1 font-semibold text-blue-400">投资建议</h3>
                      <p className="text-sm text-gray-300">
                        建议执行前再次确认钱包余额、滑点和链上手续费。
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          </div>

          <div className="space-y-8">
            <Card className="p-6">
              <h2 className="mb-4 text-lg font-bold text-white">策略信息</h2>
              <div className="space-y-4">
                <div>
                  <div className="mb-1 text-sm text-gray-400">风险等级</div>
                  <div className="text-xl font-bold text-white">{displayRisk}</div>
                </div>
                <div>
                  <div className="mb-1 text-sm text-gray-400">预期收益</div>
                  <div className="text-xl font-bold text-green-400">
                    {strategy.estimated_apy ? `${strategy.estimated_apy.toFixed(1)}%` : 'N/A'}
                  </div>
                </div>
                <div>
                  <div className="mb-1 text-sm text-gray-400">状态</div>
                  <div className={`text-xl font-bold capitalize ${statusColor[strategy.status] || 'text-white'}`}>
                    {strategy.status}
                  </div>
                </div>
                <div>
                  <div className="mb-1 text-sm text-gray-400">安全评分</div>
                  <div className="text-xl font-bold text-white">
                    {typeof strategy.risk_assessment?.score === 'number'
                      ? strategy.risk_assessment.score
                      : 'N/A'}
                  </div>
                </div>
              </div>
            </Card>

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
                  <span className="text-sm text-gray-400">策略类型</span>
                  <span className="text-sm capitalize text-white">{strategy.strategy_type}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">投入币种</span>
                  <span className="text-sm text-white">{strategy.input_token}</span>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <h2 className="mb-4 text-lg font-bold text-white">风控检查</h2>
              <div className="space-y-3">
                {checks.length ? (
                  checks.map((check, index) => (
                    <div key={`${check.item}-${index}`} className="rounded-lg bg-gray-900 p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-white">{check.item}</span>
                        <span className="text-xs uppercase text-gray-400">{check.status}</span>
                      </div>
                      <p className="mt-1 text-xs text-gray-500">{check.detail}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-gray-400">暂无风控检查明细</p>
                )}
              </div>
            </Card>

            {transaction && (
              <Card className="border border-cyan-500/30 bg-cyan-500/10 p-6">
                <h2 className="mb-4 text-lg font-bold text-white">最近执行结果</h2>
                <div className="space-y-3 text-sm text-gray-300">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">交易类型</span>
                    <span>{transaction.tx_type}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">状态</span>
                    <span>{transaction.status}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">金额</span>
                    <span>{transaction.amount || 'N/A'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">网络</span>
                    <span>{transaction.network}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">执行模式</span>
                    <span>{transaction.execution_mode}</span>
                  </div>
                </div>

                <div className="mt-5 rounded-lg border border-gray-800 bg-gray-900/70 p-4">
                  <h3 className="mb-3 text-sm font-semibold text-white">模拟 / 预构建信息</h3>
                  <div className="space-y-2 text-sm text-gray-300">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">模拟状态</span>
                      <span>{simulation.simulated ? '已模拟' : '未模拟'}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">结果模式</span>
                      <span>{String(simulationMode || txPayload.execution_mode || 'unknown')}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">预估手续费</span>
                      <span>
                        {estimatedFee != null ? `${estimatedFee} SOL` : 'N/A'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">钱包签名</span>
                      <span>{txPayload.simulation_only ? '当前不会拉起' : '可尝试拉起'}</span>
                    </div>
                    {simulationNote && <p className="pt-2 text-xs text-gray-400">{simulationNote}</p>}
                    {nextStepHint && <p className="pt-2 text-xs text-indigo-300">{nextStepHint}</p>}
                    {simulationNetworkHint && (
                      <p className="pt-2 text-xs text-yellow-400">{simulationNetworkHint}</p>
                    )}
                    {simulation.success === false && simulationError && (
                      <p className="pt-2 text-xs text-red-400">{simulationError}</p>
                    )}
                    {typeof txPayload.swap_transaction_base64 === 'string' && (
                      <p className="pt-2 text-xs text-emerald-400">
                        已生成真实待签名交易，可继续对接钱包签名发送。
                      </p>
                    )}
                  </div>
                </div>

                {previewPayload && (
                  <div className="mt-5 rounded-lg border border-indigo-500/20 bg-indigo-500/10 p-4">
                    <h3 className="mb-2 text-sm font-semibold text-white">
                      {previewPayload.headline || '协议执行预览'}
                    </h3>
                    {previewPayload.summary && (
                      <p className="text-sm text-gray-200">{previewPayload.summary}</p>
                    )}
                    {previewPayload.steps && previewPayload.steps.length > 0 && (
                      <ol className="mt-3 space-y-2 text-sm text-gray-300">
                        {previewPayload.steps.map((step, index) => (
                          <li key={`${step}-${index}`}>
                            {index + 1}. {step}
                          </li>
                        ))}
                      </ol>
                    )}
                  </div>
                )}
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
