'use client'

import { Card } from '@/components/ui/Card'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { PnLRecord } from '@/types/analysis'

interface PnLTabProps {
  pnlData: PnLRecord[]
}

export function PnLTab({ pnlData }: PnLTabProps) {
  const latestPnL = pnlData[pnlData.length - 1]

  return (
    <div className="space-y-6">
      {/* 核心指标 */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <Card className="bg-gray-800 p-6">
          <p className="text-sm text-gray-400">总累计收益</p>
          <p
            className={`mt-2 text-2xl font-bold ${latestPnL?.profitUsd >= 0 ? 'text-green-400' : 'text-red-400'}`}
          >
            {latestPnL?.profitUsd >= 0 ? '+' : ''}${latestPnL?.profitUsd.toLocaleString()}
          </p>
        </Card>
        <Card className="bg-gray-800 p-6">
          <p className="text-sm text-gray-400">综合收益率 (ROI)</p>
          <p
            className={`mt-2 text-2xl font-bold ${latestPnL?.roi >= 0 ? 'text-green-400' : 'text-red-400'}`}
          >
            {latestPnL?.roi >= 0 ? '+' : ''}
            {latestPnL?.roi}%
          </p>
        </Card>
        <Card className="bg-gray-800 p-6">
          <p className="text-sm text-gray-400">胜率统计</p>
          <p className="mt-2 text-2xl font-bold text-white">68%</p>
        </Card>
      </div>

      {/* 收益折线图 */}
      <Card className="p-6">
        <h3 className="mb-4 text-lg font-bold text-white">历史收益趋势</h3>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={pnlData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10B981" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" stroke="#9CA3AF" />
              <YAxis stroke="#9CA3AF" />
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                }}
                itemStyle={{ color: '#10B981' }}
              />
              <Area
                type="monotone"
                dataKey="profitUsd"
                stroke="#10B981"
                fillOpacity={1}
                fill="url(#colorProfit)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  )
}
