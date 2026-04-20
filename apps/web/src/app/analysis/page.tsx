'use client'

import { useTranslation } from '@/hooks/useTranslation'
import { Card } from '@/components/ui/Card'
import { AnalysisTabs } from '@/components/analysis/AnalysisTabs'
import { mockAssets, mockPnLData, mockRiskDiagnosis } from '@/data/mockAnalysis'

export default function AssetAnalysisPage() {
  const { t: _t } = useTranslation()

  // 模拟从后端/React Query获取数据
  const assets = mockAssets
  const pnlData = mockPnLData
  const diagnosis = mockRiskDiagnosis

  const totalValue = assets.reduce((sum, a) => sum + a.valueUsd, 0)
  const latestPnL = pnlData[pnlData.length - 1]

  return (
    <div className="min-h-screen bg-gray-950 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">资产诊断分析</h1>
          <p className="mt-2 text-gray-400">全方位分析您的链上资产健康状况</p>
        </div>

        {/* 顶部概览卡片 (StatCard) */}
        <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-3">
          <Card className="border border-gray-800 bg-gray-900 p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-300">总资产价值</h3>
              <span className="text-2xl">💰</span>
            </div>
            <p className="mb-2 text-3xl font-bold text-white">${totalValue.toLocaleString()}</p>
            <p className="text-sm text-green-400">+5.2% (24h)</p>
          </Card>

          <Card className="border border-gray-800 bg-gray-900 p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-300">累计盈亏</h3>
              <span className="text-2xl">📊</span>
            </div>
            <p
              className={`mb-2 text-3xl font-bold ${latestPnL?.profitUsd >= 0 ? 'text-green-400' : 'text-red-400'}`}
            >
              {latestPnL?.profitUsd >= 0 ? '+' : ''}${latestPnL?.profitUsd.toLocaleString()}
            </p>
            <p className="text-sm text-gray-400">ROI: {latestPnL?.roi}%</p>
          </Card>

          <Card className="border border-gray-800 bg-gray-900 p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-300">综合健康分</h3>
              <span className="text-2xl">🛡️</span>
            </div>
            <p
              className={`mb-2 text-3xl font-bold ${
                diagnosis.healthScore >= 80
                  ? 'text-green-400'
                  : diagnosis.healthScore >= 60
                    ? 'text-yellow-400'
                    : 'text-red-400'
              }`}
            >
              {diagnosis.healthScore}
            </p>
            <p className="text-sm text-gray-400">{diagnosis.warnings.length}个风险项待处理</p>
          </Card>
        </div>

        {/* 详细诊断与分析 Tab 区 */}
        <AnalysisTabs assets={assets} pnlData={pnlData} diagnosis={diagnosis} />
      </div>
    </div>
  )
}
