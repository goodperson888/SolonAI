'use client'

import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { useTranslation } from '@/hooks/useTranslation'
import Link from 'next/link'

interface StrategyCardProps {
  id?: string
  name: string
  protocol: string
  expectedAPY: number
  riskLevel: 'low' | 'medium' | 'high'
  lockPeriod: string
  steps: string[]
  deployed?: boolean
  deployedAmount?: number
  detailsHref?: string
  actionHref?: string
  onActionClick?: () => void
  statusLabel?: string
  executionLabel?: string
  executionHint?: string
  primaryActionLabel?: string
}

export const StrategyCard: React.FC<StrategyCardProps> = ({
  id,
  name,
  protocol,
  expectedAPY,
  riskLevel,
  lockPeriod,
  steps,
  deployed = false,
  deployedAmount,
  detailsHref,
  actionHref,
  onActionClick,
  statusLabel,
  executionLabel,
  executionHint,
  primaryActionLabel,
}) => {
  const { t } = useTranslation()
  const defaultHref = id ? `/strategy/${id}` : '/strategy'
  const resolvedDetailsHref = detailsHref || defaultHref
  const resolvedActionHref = actionHref || defaultHref

  const riskColors = {
    low: 'text-green-500 bg-green-500/10',
    medium: 'text-yellow-500 bg-yellow-500/10',
    high: 'text-red-500 bg-red-500/10',
  }

  const riskLabels = {
    low: t('common.low'),
    medium: t('common.medium'),
    high: t('common.high'),
  }

  return (
    <Card hover className="flex h-full flex-col">
      <div className="flex h-full flex-col gap-4">
        {/* Header */}
        <div>
          <h3 className="text-xl font-semibold text-white">{name}</h3>
          <p className="mt-1 text-sm text-gray-400">{protocol}</p>
          {(statusLabel || executionLabel) && (
            <div className="mt-3 flex flex-wrap gap-2">
              {statusLabel && (
                <span className="rounded-full bg-white/5 px-2.5 py-1 text-xs text-gray-300">
                  {statusLabel}
                </span>
              )}
              {executionLabel && (
                <span className="rounded-full bg-indigo-500/10 px-2.5 py-1 text-xs text-indigo-300">
                  {executionLabel}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-lg bg-gray-800 p-3 text-center">
            <p className="text-sm text-gray-400">{t('strategy.expectedAPY')}</p>
            <p className="mt-1 text-2xl font-bold text-green-500">{expectedAPY}%</p>
          </div>

          <div className="rounded-lg bg-gray-800 p-3 text-center">
            <p className="text-sm text-gray-400">{t('strategy.risk')}</p>
            <span
              className={`mt-1 inline-block rounded-full px-3 py-1 text-sm font-medium ${riskColors[riskLevel]}`}
            >
              {riskLabels[riskLevel]}
            </span>
          </div>

          <div className="rounded-lg bg-gray-800 p-3 text-center">
            <p className="text-sm text-gray-400">{t('strategy.lockPeriod')}</p>
            <p className="mt-1 text-lg font-semibold text-white">{lockPeriod}</p>
          </div>
        </div>

        {/* Steps */}
        <div className="flex-1">
          <p className="mb-2 text-sm font-medium text-gray-300">操作步骤:</p>
          <ol className="min-h-[84px] space-y-1">
            {steps.slice(0, 3).map((step, index) => (
              <li key={index} className="text-sm text-gray-400">
                {index + 1}. {step}
              </li>
            ))}
            {steps.length === 0 && <li className="text-sm text-gray-500">暂无执行步骤</li>}
          </ol>
        </div>

        {/* Deployed Status */}
        {deployed && deployedAmount && (
          <div className="rounded-lg border border-indigo-500/30 bg-indigo-500/10 p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-indigo-400">已部署</span>
              <span className="text-sm font-semibold text-white">{deployedAmount} USDC</span>
            </div>
          </div>
        )}

        {executionHint && (
          <div className="rounded-lg border border-gray-800 bg-gray-900/70 p-3 text-sm text-gray-300">
            {executionHint}
          </div>
        )}

        {/* Actions */}
        <div className="mt-auto flex space-x-3 pt-2">
          <Link href={resolvedDetailsHref} className="flex-1">
            <Button variant="outline" size="md" className="w-full">
              {t('strategy.viewDetails')}
            </Button>
          </Link>
          {onActionClick ? (
            <Button variant="primary" size="md" className="flex-1" onClick={onActionClick}>
              {primaryActionLabel || (deployed ? '管理' : t('strategy.execute'))}
            </Button>
          ) : (
            <Link href={resolvedActionHref} className="flex-1">
              <Button variant="primary" size="md" className="w-full">
                {primaryActionLabel || (deployed ? '管理' : t('strategy.execute'))}
              </Button>
            </Link>
          )}
        </div>
      </div>
    </Card>
  )
}
