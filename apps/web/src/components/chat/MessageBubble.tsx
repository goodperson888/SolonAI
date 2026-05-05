'use client'

import Link from 'next/link'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ChatMessageData, ChatStrategyStep } from '@/lib/api-client'
import { Button } from '@/components/ui/Button'

interface RagSource {
  filename: string
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  intent?: string
  data?: ChatMessageData
  ragSources?: RagSource[]
  agentStatus?: {
    agent: string
    status: 'running' | 'done'
    message: string
  }[]
}

interface MessageBubbleProps {
  message: Message
  onQuickAction?: (prompt: string) => void
  onApprovalAction?: (threadId: string, approved: boolean) => void
  onSaveStrategy?: (messageId: string, data: ChatMessageData, content: string) => void
  savingStrategyMessageId?: string | null
  approvingThreadId?: string | null
}

function renderStepLabel(step: ChatStrategyStep, _index: number) {
  return step.description || `${step.action || '操作'} · ${step.protocol || '协议未定'}`
}

function inferStrategyProtocol(strategy?: ChatMessageData['strategy']) {
  if (!strategy) return '待定'
  const direct = strategy.protocol || strategy.protocol_name
  if (direct && String(direct).trim()) return String(direct).trim()
  const firstStepProtocol = strategy.steps?.find((step) => step.protocol)?.protocol
  if (firstStepProtocol && String(firstStepProtocol).trim()) {
    return String(firstStepProtocol).trim()
  }
  const firstProtocol = strategy.protocols?.find((item) => item && String(item).trim())
  if (firstProtocol) return String(firstProtocol).trim()
  return '待定'
}

function resolveExecutionCopy(protocol?: string) {
  const normalized = (protocol || '').toLowerCase()
  if (normalized === 'jupiter' || normalized === 'raydium') {
    return {
      badge: '主网下可尝试签名',
      cta: '去查看执行详情',
      hint: '这类策略在主网下更接近真实执行链路。',
    }
  }
  if (normalized === 'marginfi' || normalized === 'kamino' || normalized === 'orca' || normalized === 'solend') {
    return {
      badge: '当前以参数预览为主',
      cta: '去查看执行预览',
      hint: '当前会先展示协议参数、费用估计和风险说明。',
    }
  }
  return {
    badge: '查看执行详情',
    cta: '去策略工作台',
    hint: '你可以先查看详情，再决定是否继续执行。',
  }
}

function LoadingRows({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="h-9 animate-pulse rounded-lg bg-white/5" />
      ))}
    </div>
  )
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  onQuickAction,
  onApprovalAction,
  onSaveStrategy,
  savingStrategyMessageId,
  approvingThreadId,
}) => {
  const isUser = message.role === 'user'
  const strategy = message.data?.strategy
  const risk = message.data?.risk_assessment
  const walletAssets = message.data?.wallet_assets
  const transaction = message.data?.transaction
  const approvalPreview = message.data?.approval_preview
  const streamProgress = message.data?.stream_progress
  const threadId = message.data?.thread_id
  const isInterrupted = message.data?.interrupted !== false
  const savedStrategyId = message.data?.saved_strategy_id
  const isApproving = approvingThreadId != null && approvingThreadId === threadId
  const isSavingStrategy = savingStrategyMessageId != null && savingStrategyMessageId === message.id
  const strategyExecutionHref = savedStrategyId ? `/strategy/${savedStrategyId}` : '/strategy'
  const totalValueUsd = message.data?.total_value_usd
  const resolvedProtocol = inferStrategyProtocol(strategy)
  const executionCopy = resolveExecutionCopy(resolvedProtocol)

  // 清除 AI 回复中的 HTML 标签（如 <br>）
  const cleanContent = isUser ? message.content : message.content.replace(/<[^>]*>/g, '')
  const hasRenderableContent = cleanContent.trim().length > 0
  const assetNarrative =
    walletAssets && walletAssets.length > 0
      ? `当前检测到 ${walletAssets.length} 项资产${
          typeof totalValueUsd === 'number' ? `，总估值约 $${totalValueUsd.toFixed(2)}` : ''
        }。`
      : '正在整理你的资产快照与估值信息。'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`${isUser ? 'order-2 max-w-[70%]' : 'order-1 max-w-[92%]'}`}>
        {/* Avatar */}
        <div className="flex items-start space-x-3">
          {!isUser && (
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-600 to-purple-600">
              <span className="text-sm font-semibold text-white">AI</span>
            </div>
          )}

          {/* Message Content */}
          <div className="flex-1">
            <div
              className={`rounded-2xl ${
                isUser
                  ? 'bg-gradient-to-br from-indigo-600 to-purple-600 px-4 py-3 text-white'
                  : 'bg-gray-800 px-4 py-3 text-gray-100'
              }`}
            >
              {/* Agent Status - 显示在消息内容上方 */}
              {!isUser && message.agentStatus && message.agentStatus.length > 0 && (
                <div className="mb-2 flex items-center gap-2 text-xs text-indigo-400">
                  {message.agentStatus.map((agent, i) => (
                    <div key={i} className="flex items-center gap-1.5">
                      {agent.status === 'running' && (
                        <>
                          <svg className="h-3 w-3 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                            />
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            />
                          </svg>
                          <span>{agent.message}</span>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {isUser ? (
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
              ) : (
                <div className="space-y-4">
                  {hasRenderableContent ? (
                    <div className="prose prose-invert prose-sm max-w-none [&_h1]:mb-3 [&_h2]:mb-3 [&_h3]:mb-3 [&_ol:last-child]:mb-0 [&_ol]:mb-3 [&_p:last-child]:mb-0 [&_p]:mb-3 [&_table]:border-collapse [&_table]:border [&_table]:border-gray-600 [&_td]:border [&_td]:border-gray-600 [&_td]:px-3 [&_td]:py-2 [&_th]:border [&_th]:border-gray-600 [&_th]:bg-gray-700/50 [&_th]:px-3 [&_th]:py-2 [&_ul:last-child]:mb-0 [&_ul]:mb-3">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          br: () => null,
                        }}
                      >
                        {cleanContent}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    (walletAssets?.length || strategy || risk) && (
                      <p className="text-sm leading-relaxed text-gray-200">
                        {walletAssets?.length
                          ? assetNarrative
                          : '正在整理这次分析结果，请看下面的结构化卡片。'}
                      </p>
                    )
                  )}

                  {(strategy || streamProgress?.strategy) && (
                    <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/10 p-4">
                      <div className="mb-3 flex items-start justify-between gap-3">
                        <div>
                          <h4 className="font-semibold text-white">
                            {strategy?.title || strategy?.strategy_name || '策略草案'}
                          </h4>
                          <p className="mt-1 text-xs text-gray-300">
                            协议: {resolvedProtocol}
                          </p>
                          <div className="mt-2">
                            <span className="rounded-full bg-indigo-500/15 px-2.5 py-1 text-xs text-indigo-200">
                              {executionCopy.badge}
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-green-400">
                            {typeof (strategy?.estimated_apy ?? strategy?.expected_apy) === 'number'
                              ? `${(strategy?.estimated_apy ?? strategy?.expected_apy)?.toFixed(1)}%`
                              : 'N/A'}
                          </div>
                          <div className="text-xs text-gray-400">预期收益</div>
                        </div>
                      </div>

                      {strategy?.steps && strategy.steps.length > 0 ? (
                        <div className="space-y-2">
                          {strategy.steps.slice(0, 3).map((step, index) => (
                            <div
                              key={`${step.protocol}-${step.action}-${index}`}
                              className="rounded-lg bg-gray-900/60 px-3 py-2 text-sm text-gray-200"
                            >
                              <span className="mr-2 text-indigo-300">{index + 1}.</span>
                              {renderStepLabel(step, index)}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <LoadingRows count={2} />
                      )}

                      {strategy?.steps && strategy.steps.length > 0 && (
                        <div className="mt-4 flex flex-wrap gap-2">
                          {onQuickAction && (
                            <>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() =>
                                  onQuickAction('把这套策略调整得更稳健一点，并解释为什么这么改')
                                }
                              >
                                更稳健一点
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() =>
                                  onQuickAction('把这套策略收益做高一点，但请明确新增风险')
                                }
                              >
                                提高收益
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() =>
                                  onQuickAction('基于这套策略重新生成一个版本，并保持可随时退出')
                                }
                              >
                                重新生成
                              </Button>
                            </>
                          )}
                          {strategy && onSaveStrategy && !savedStrategyId && (
                            <Button
                              variant="primary"
                              size="sm"
                              disabled={isSavingStrategy}
                              onClick={() =>
                                onSaveStrategy(message.id, message.data || {}, cleanContent)
                              }
                            >
                              {isSavingStrategy ? '保存中...' : '保存到策略工作台'}
                            </Button>
                          )}
                          {savedStrategyId && (
                            <Link href={`/strategy/${savedStrategyId}`}>
                              <Button variant="primary" size="sm">
                                查看已保存策略
                              </Button>
                            </Link>
                          )}
                          <Link href={strategyExecutionHref}>
                            <Button variant="outline" size="sm">
                              {savedStrategyId ? executionCopy.cta : '去策略工作台'}
                            </Button>
                          </Link>
                          <Link href="/strategy">
                            <Button variant="ghost" size="sm">
                              查看全部策略
                            </Button>
                          </Link>
                        </div>
                      )}
                      <p className="mt-3 text-xs text-gray-400">{executionCopy.hint}</p>
                    </div>
                  )}

                  {(risk || streamProgress?.risk_assessment) && (
                    <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-4">
                      <div className="mb-2 flex items-center justify-between">
                        <h4 className="font-semibold text-white">风险摘要</h4>
                        <span className="text-sm font-medium text-yellow-300">
                          {risk?.risk_level || 'unknown'} / {risk?.score ?? 'N/A'}
                        </span>
                      </div>
                      {risk?.warnings && risk.warnings.length > 0 ? (
                        <div className="space-y-1 text-sm text-gray-200">
                          {risk.warnings.slice(0, 3).map((warning, index) => (
                            <p key={`${warning}-${index}`}>- {warning}</p>
                          ))}
                        </div>
                      ) : (
                        <LoadingRows count={2} />
                      )}
                    </div>
                  )}

                  {(walletAssets || streamProgress?.wallet_assets) && (
                    <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4">
                      <div className="mb-2 flex items-center justify-between">
                        <h4 className="font-semibold text-white">资产摘要</h4>
                        <span className="text-sm text-emerald-300">
                          {typeof totalValueUsd === 'number'
                            ? `$${totalValueUsd.toFixed(2)}`
                            : '估值待获取'}
                        </span>
                      </div>
                      <p className="mb-3 text-sm text-gray-200">{assetNarrative}</p>
                      {walletAssets && walletAssets.length > 0 ? (
                        <div className="space-y-1 text-sm text-gray-200">
                          {walletAssets.slice(0, 4).map((asset, index) => (
                            <div key={`${asset.symbol}-${index}`} className="flex justify-between">
                              <span>{asset.symbol || 'UNKNOWN'}</span>
                              <span>
                                {asset.balance ?? 0}
                                {typeof asset.usd_value === 'number'
                                  ? ` · $${asset.usd_value.toFixed(2)}`
                                  : ' · 估值待获取'}
                              </span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <LoadingRows count={2} />
                      )}
                    </div>
                  )}

                  {transaction && (
                    <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-4">
                      <div className="mb-2 flex items-center justify-between">
                        <h4 className="font-semibold text-white">执行结果</h4>
                        <span className="text-sm text-cyan-300">
                          {transaction.status || 'prepared'}
                        </span>
                      </div>
                      <div className="space-y-2 text-sm text-gray-200">
                        <div className="flex justify-between gap-4">
                          <span className="text-gray-400">类型</span>
                          <span>{transaction.tx_type || '预览执行'}</span>
                        </div>
                        <div className="flex justify-between gap-4">
                          <span className="text-gray-400">网络</span>
                          <span>{transaction.network || 'mainnet'}</span>
                        </div>
                        <div className="flex justify-between gap-4">
                          <span className="text-gray-400">模式</span>
                          <span>{transaction.execution_mode || 'auto'}</span>
                        </div>
                        {transaction.simulation_result &&
                          typeof transaction.simulation_result === 'object' && (
                            <>
                              {'note' in transaction.simulation_result &&
                                typeof transaction.simulation_result.note === 'string' && (
                                  <p className="pt-2 text-sm text-gray-200">
                                    {transaction.simulation_result.note}
                                  </p>
                                )}
                              {'network_hint' in transaction.simulation_result &&
                                typeof transaction.simulation_result.network_hint === 'string' && (
                                  <p className="text-xs text-yellow-300">
                                    {transaction.simulation_result.network_hint}
                                  </p>
                                )}
                              {'estimated_fee_sol' in transaction.simulation_result &&
                                typeof transaction.simulation_result.estimated_fee_sol === 'number' && (
                                  <p className="text-xs text-gray-300">
                                    预估手续费：{transaction.simulation_result.estimated_fee_sol} SOL
                                  </p>
                                )}
                            </>
                          )}
                      </div>
                    </div>
                  )}

                  {(approvalPreview || streamProgress?.approval_preview) && isInterrupted && (
                    <div className="rounded-xl border border-blue-500/30 bg-blue-500/10 p-4">
                      <h4 className="mb-2 font-semibold text-white">待确认操作</h4>
                      <p className="mb-3 text-sm text-gray-200">
                        {approvalPreview?.message || '请确认当前策略后继续执行。'}
                      </p>
                      {approvalPreview?.steps && approvalPreview.steps.length > 0 ? (
                        <div className="mb-3 space-y-1 text-sm text-gray-200">
                          {approvalPreview.steps.slice(0, 3).map((step, index) => (
                            <p key={`${step.protocol}-${step.action}-${index}`}>
                              {index + 1}. {renderStepLabel(step, index)}
                            </p>
                          ))}
                        </div>
                      ) : (
                        <div className="mb-3">
                          <LoadingRows count={2} />
                        </div>
                      )}
                      {threadId &&
                        onApprovalAction &&
                        approvalPreview?.steps &&
                        approvalPreview.steps.length > 0 && (
                          <div className="flex flex-wrap gap-2">
                            <Button
                              variant="primary"
                              size="sm"
                              disabled={isApproving}
                              onClick={() => onApprovalAction(threadId, true)}
                            >
                              {isApproving ? '处理中...' : '确认执行'}
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={isApproving}
                              onClick={() => onApprovalAction(threadId, false)}
                            >
                              取消
                            </Button>
                          </div>
                        )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Agent Status - 移除原来在消息气泡外的显示 */}
            {!isUser && message.ragSources && message.ragSources.length > 0 && (
              <div className="mt-1.5 flex flex-wrap gap-1.5 px-2">
                {message.ragSources.map((src, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 rounded-md bg-indigo-500/10 px-2 py-0.5 text-xs text-indigo-400"
                  >
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    {src.filename}
                  </span>
                ))}
              </div>
            )}

            {/* Timestamp */}
            <p className="mt-1 px-2 text-xs text-gray-500">
              {message.timestamp.toLocaleTimeString('zh-CN', {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          </div>

          {isUser && (
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gray-700">
              <span className="text-sm text-white">👤</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
