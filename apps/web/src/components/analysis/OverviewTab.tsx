'use client'

import { Card } from '@/components/ui/Card'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import type { Asset } from '@/types/analysis'

interface OverviewTabProps {
  assets: Asset[]
}

export function OverviewTab({ assets }: OverviewTabProps) {
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#A28CFE']

  const chartData = assets.map((a, i) => ({
    name: a.symbol,
    value: a.valueUsd,
    color: a.color || COLORS[i % COLORS.length],
  }))

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      {/* 资产分布饼图 */}
      <Card className="p-6">
        <h3 className="mb-4 text-lg font-bold text-white">资产分布</h3>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: number) => [`$${value.toFixed(2)}`, 'Value']}
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Legend verticalAlign="bottom" height={36} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* 资产列表 */}
      <Card className="p-6">
        <h3 className="mb-4 text-lg font-bold text-white">资产列表</h3>
        <div className="space-y-4">
          {assets.map((asset) => (
            <div
              key={asset.symbol}
              className="flex items-center justify-between rounded-lg bg-gray-800 p-4"
            >
              <div>
                <p className="font-medium text-white">{asset.symbol}</p>
                <p className="mt-1 text-sm text-gray-400">数量: {asset.balance}</p>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-white">${asset.valueUsd.toLocaleString()}</p>
                <p
                  className={`text-sm ${asset.change24h >= 0 ? 'text-green-400' : 'text-red-400'}`}
                >
                  {asset.change24h >= 0 ? '+' : ''}
                  {asset.change24h}% (24h)
                </p>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
