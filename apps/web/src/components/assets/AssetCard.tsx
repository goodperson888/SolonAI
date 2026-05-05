'use client'

import { Card } from '@/components/ui/Card'

interface AssetCardProps {
  icon: string
  symbol: string
  name: string
  amount: number
  value?: number
  change24h?: number
}

export const AssetCard: React.FC<AssetCardProps> = ({
  icon,
  symbol,
  name,
  amount,
  value = 0,
  change24h = 0,
}) => {
  const isPositive = change24h >= 0

  return (
    <Card hover className="flex h-full cursor-pointer flex-col">
      <div className="flex h-full flex-col justify-between gap-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center space-x-4">
          {/* Token Icon */}
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 text-xl font-bold text-white">
              {icon}
            </div>

            {/* Token Info */}
            <div className="min-w-0">
              <h3 className="truncate text-lg font-semibold text-white">{symbol}</h3>
              <p className="truncate text-sm text-gray-400">{name}</p>
              <p className="mt-1 text-sm text-gray-400">
                {amount.toLocaleString()} {symbol}
              </p>
            </div>
          </div>

          {/* Value & Change */}
          <div className="text-right">
            <p className="text-lg font-semibold text-white">${value.toLocaleString()}</p>
            <div
              className={`mt-1 flex items-center justify-end space-x-1 ${
                isPositive ? 'text-green-500' : 'text-red-500'
              }`}
            >
              <span className="text-sm">
                {isPositive ? '↑' : '↓'} {Math.abs(change24h).toFixed(2)}%
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 rounded-lg border border-gray-800 bg-gray-950/60 p-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-500">持仓数量</p>
            <p className="mt-1 text-sm font-medium text-white">{amount.toLocaleString()}</p>
          </div>
          <div className="text-right">
            <p className="text-xs uppercase tracking-wide text-gray-500">当前估值</p>
            <p className="mt-1 text-sm font-medium text-white">${value.toLocaleString()}</p>
          </div>
        </div>
      </div>
    </Card>
  )
}
