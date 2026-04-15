'use client'

import { Card } from '@/components/ui/Card'

interface StatCardProps {
  title: string
  value: string | number
  change?: number
  icon?: string
  trend?: 'up' | 'down' | 'neutral'
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  icon,
  trend = 'neutral',
}) => {
  const trendColors = {
    up: 'text-green-500',
    down: 'text-red-500',
    neutral: 'text-gray-400',
  }

  const trendIcons = {
    up: '↑',
    down: '↓',
    neutral: '→',
  }

  return (
    <Card hover>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="mb-2 text-sm text-gray-400">{title}</p>
          <p className="mb-1 text-3xl font-bold text-white">{value}</p>
          {change !== undefined && (
            <div className="flex items-center space-x-1">
              <span className={`text-sm font-medium ${trendColors[trend]}`}>
                {trendIcons[trend]} {Math.abs(change)}%
              </span>
              <span className="text-xs text-gray-500">24h</span>
            </div>
          )}
        </div>

        {icon && (
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-purple-600">
            <span className="text-2xl">{icon}</span>
          </div>
        )}
      </div>
    </Card>
  )
}
