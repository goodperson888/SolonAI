'use client'

import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { useTranslation } from '@/hooks/useTranslation'

interface StrategyCardProps {
  name: string
  protocol: string
  expectedAPY: number
  riskLevel: 'low' | 'medium' | 'high'
  lockPeriod: string
  steps: string[]
  deployed?: boolean
  deployedAmount?: number
}

export const StrategyCard: React.FC<StrategyCardProps> = ({
  name,
  protocol,
  expectedAPY,
  riskLevel,
  lockPeriod,
  steps,
  deployed = false,
  deployedAmount,
}) => {
  const { t } = useTranslation()

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
    <Card hover>
      <div className="space-y-4">
        {/* Header */}
        <div>
          <h3 className="text-xl font-semibold text-white">{name}</h3>
          <p className="mt-1 text-sm text-gray-400">{protocol}</p>
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
        <div>
          <p className="mb-2 text-sm font-medium text-gray-300">操作步骤:</p>
          <ol className="space-y-1">
            {steps.map((step, index) => (
              <li key={index} className="text-sm text-gray-400">
                {index + 1}. {step}
              </li>
            ))}
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

        {/* Actions */}
        <div className="flex space-x-3">
          <Button variant="outline" size="md" className="flex-1">
            {t('strategy.viewDetails')}
          </Button>
          <Button variant="primary" size="md" className="flex-1">
            {deployed ? '管理' : t('strategy.execute')}
          </Button>
        </div>
      </div>
    </Card>
  )
}
