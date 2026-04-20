'use client'

import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from 'recharts'
import type { RiskDiagnosis } from '@/types/analysis'

interface RiskTabProps {
  diagnosis: RiskDiagnosis
}

export function RiskTab({ diagnosis }: RiskTabProps) {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      {/* 雷达图与健康分 */}
      <Card className="p-6">
        <div className="mb-6 flex items-center justify-between">
          <h3 className="text-lg font-bold text-white">风险维度雷达图</h3>
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">健康分:</span>
            <span
              className={`text-xl font-bold ${diagnosis.healthScore > 80 ? 'text-green-400' : diagnosis.healthScore > 60 ? 'text-yellow-400' : 'text-red-400'}`}
            >
              {diagnosis.healthScore}
            </span>
          </div>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={diagnosis.dimensions}>
              <PolarGrid stroke="#374151" />
              <PolarAngleAxis dataKey="category" stroke="#9CA3AF" />
              <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#4B5563" />
              <Radar
                name="风险得分"
                dataKey="score"
                stroke="#8B5CF6"
                fill="#8B5CF6"
                fillOpacity={0.6}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* 风险报告与AI建议 */}
      <div className="space-y-6">
        <Card className="p-6">
          <h3 className="mb-4 text-lg font-bold text-white">AI 诊断报告</h3>
          <div className="rounded-lg bg-gray-800 p-4 text-gray-300">
            <p className="leading-relaxed">{diagnosis.aiAdvice}</p>
          </div>
        </Card>

        <Card className="border-red-500/30 p-6">
          <h3 className="mb-4 text-lg font-bold text-red-400">风险预警</h3>
          {diagnosis.warnings.length > 0 ? (
            <div className="space-y-3">
              {diagnosis.warnings.map((warning, index) => (
                <div key={index} className="flex items-start gap-3 rounded-lg bg-red-500/10 p-3">
                  <span className="mt-0.5 text-red-400">⚠️</span>
                  <p className="text-sm text-gray-200">{warning}</p>
                </div>
              ))}
              <Button
                variant="outline"
                className="mt-4 w-full border-red-500/50 text-red-400 hover:bg-red-500/10"
              >
                一键处理风险
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2 rounded-lg bg-green-500/10 p-4 text-green-400">
              <span>✅</span>
              <span>当前未检测到明显风险项，您的资产很安全。</span>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
