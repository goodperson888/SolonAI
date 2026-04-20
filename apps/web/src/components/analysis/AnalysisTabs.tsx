'use client'

import { useState } from 'react'
import { OverviewTab } from './OverviewTab'
import { PnLTab } from './PnLTab'
import { RiskTab } from './RiskTab'
import type { Asset, PnLRecord, RiskDiagnosis } from '@/types/analysis'

interface AnalysisTabsProps {
  assets: Asset[]
  pnlData: PnLRecord[]
  diagnosis: RiskDiagnosis
}

export function AnalysisTabs({ assets, pnlData, diagnosis }: AnalysisTabsProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'pnl' | 'risk'>('overview')

  return (
    <div className="w-full">
      {/* 选项卡导航 */}
      <div className="mb-6 flex space-x-1 rounded-xl bg-gray-800 p-1">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex-1 rounded-lg py-2.5 text-sm font-medium leading-5 transition-colors ${
            activeTab === 'overview'
              ? 'bg-gray-900 text-white shadow'
              : 'text-gray-400 hover:bg-gray-700/50 hover:text-white'
          }`}
        >
          资产总览
        </button>
        <button
          onClick={() => setActiveTab('pnl')}
          className={`flex-1 rounded-lg py-2.5 text-sm font-medium leading-5 transition-colors ${
            activeTab === 'pnl'
              ? 'bg-gray-900 text-white shadow'
              : 'text-gray-400 hover:bg-gray-700/50 hover:text-white'
          }`}
        >
          盈亏分析
        </button>
        <button
          onClick={() => setActiveTab('risk')}
          className={`flex-1 rounded-lg py-2.5 text-sm font-medium leading-5 transition-colors ${
            activeTab === 'risk'
              ? 'bg-gray-900 text-white shadow'
              : 'text-gray-400 hover:bg-gray-700/50 hover:text-white'
          }`}
        >
          风险诊断
        </button>
      </div>

      {/* 内容区域 */}
      <div className="mt-4">
        {activeTab === 'overview' && <OverviewTab assets={assets} />}
        {activeTab === 'pnl' && <PnLTab pnlData={pnlData} />}
        {activeTab === 'risk' && <RiskTab diagnosis={diagnosis} />}
      </div>
    </div>
  )
}
