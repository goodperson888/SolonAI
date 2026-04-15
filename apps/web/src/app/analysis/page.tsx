'use client'

import { useTranslation } from '@/hooks/useTranslation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'

export default function AssetAnalysisPage() {
  const { t: _t } = useTranslation()

  return (
    <div className="min-h-screen bg-gray-950 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">资产诊断分析</h1>
          <p className="mt-2 text-gray-400">全方位分析您的链上资产健康状况</p>
        </div>

        {/* 资产概览 */}
        <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-3">
          <Card className="p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">总资产价值</h3>
              <span className="text-2xl">💰</span>
            </div>
            <p className="mb-2 text-3xl font-bold text-white">$12,458.32</p>
            <p className="text-sm text-green-400">+5.2% (24h)</p>
          </Card>

          <Card className="p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">总盈亏</h3>
              <span className="text-2xl">📊</span>
            </div>
            <p className="mb-2 text-3xl font-bold text-green-400">+$1,234.56</p>
            <p className="text-sm text-gray-400">年化收益率: 18.5%</p>
          </Card>

          <Card className="p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-white">风险评级</h3>
              <span className="text-2xl">🛡️</span>
            </div>
            <p className="mb-2 text-3xl font-bold text-yellow-400">中低</p>
            <p className="text-sm text-gray-400">2个风险项待处理</p>
          </Card>
        </div>

        {/* 盈亏分析 */}
        <Card className="mb-8 p-6">
          <h2 className="mb-6 text-xl font-bold text-white">盈亏分析</h2>

          <div className="space-y-4">
            {/* 持仓盈亏 */}
            <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
              <div>
                <p className="font-medium text-white">持仓浮动盈亏</p>
                <p className="mt-1 text-sm text-gray-400">当前持仓的未实现盈亏</p>
              </div>
              <div className="text-right">
                <p className="text-xl font-bold text-green-400">+$856.32</p>
                <p className="text-sm text-gray-400">+7.4%</p>
              </div>
            </div>

            {/* 历史交易盈亏 */}
            <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
              <div>
                <p className="font-medium text-white">历史交易盈亏</p>
                <p className="mt-1 text-sm text-gray-400">已实现的交易盈亏</p>
              </div>
              <div className="text-right">
                <p className="text-xl font-bold text-green-400">+$378.24</p>
                <p className="text-sm text-gray-400">胜率: 68%</p>
              </div>
            </div>

            {/* DeFi 收益 */}
            <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
              <div>
                <p className="font-medium text-white">DeFi 策略收益</p>
                <p className="mt-1 text-sm text-gray-400">流动性挖矿、借贷等收益</p>
              </div>
              <div className="text-right">
                <p className="text-xl font-bold text-green-400">+$124.56</p>
                <p className="text-sm text-gray-400">年化: 15.2%</p>
              </div>
            </div>
          </div>
        </Card>

        {/* 风险诊断 */}
        <Card className="mb-8 p-6">
          <h2 className="mb-6 text-xl font-bold text-white">风险诊断</h2>

          <div className="space-y-4">
            {/* 高危代币警告 */}
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">⚠️</span>
                <div className="flex-1">
                  <div className="mb-2 flex items-center justify-between">
                    <h3 className="font-semibold text-white">检测到高危代币</h3>
                    <span className="rounded bg-red-500 px-2 py-1 text-xs text-white">高风险</span>
                  </div>
                  <p className="mb-3 text-sm text-gray-300">
                    您持有的 SCAM 代币存在 rug pull 风险，建议立即处理
                  </p>
                  <Button variant="outline" size="sm">
                    立即处理
                  </Button>
                </div>
              </div>
            </div>

            {/* 无限授权警告 */}
            <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">⚡</span>
                <div className="flex-1">
                  <div className="mb-2 flex items-center justify-between">
                    <h3 className="font-semibold text-white">发现无限授权</h3>
                    <span className="rounded bg-yellow-500 px-2 py-1 text-xs text-white">
                      中风险
                    </span>
                  </div>
                  <p className="mb-3 text-sm text-gray-300">
                    3个合约拥有您的无限授权，建议撤销过期授权
                  </p>
                  <Button variant="outline" size="sm">
                    查看详情
                  </Button>
                </div>
              </div>
            </div>

            {/* 安全提示 */}
            <div className="rounded-lg border border-green-500/30 bg-green-500/10 p-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">✅</span>
                <div className="flex-1">
                  <h3 className="mb-2 font-semibold text-white">资产安全</h3>
                  <p className="text-sm text-gray-300">
                    您的主要资产（SOL、USDC）均为安全资产，无风险
                  </p>
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* 收益优化建议 */}
        <Card className="p-6">
          <h2 className="mb-6 text-xl font-bold text-white">收益优化建议</h2>

          <div className="space-y-4">
            {/* 建议1 */}
            <div className="rounded-lg bg-gray-800 p-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">💡</span>
                <div className="flex-1">
                  <h3 className="mb-2 font-semibold text-white">闲置资产生息</h3>
                  <p className="mb-3 text-sm text-gray-300">
                    您有 50 SOL 闲置资产，可存入 MarginFi 获得 4.2% 年化收益，无锁仓风险
                  </p>
                  <div className="flex items-center gap-3">
                    <Button size="sm">立即执行</Button>
                    <Button variant="outline" size="sm">
                      查看详情
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            {/* 建议2 */}
            <div className="rounded-lg bg-gray-800 p-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">💡</span>
                <div className="flex-1">
                  <h3 className="mb-2 font-semibold text-white">流动性挖矿机会</h3>
                  <p className="mb-3 text-sm text-gray-300">
                    SOL-USDC 流动性池当前 APY 18.5%，适合您的稳健型风险偏好
                  </p>
                  <div className="flex items-center gap-3">
                    <Button size="sm">立即执行</Button>
                    <Button variant="outline" size="sm">
                      查看详情
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            {/* 建议3 */}
            <div className="rounded-lg bg-gray-800 p-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">💡</span>
                <div className="flex-1">
                  <h3 className="mb-2 font-semibold text-white">资产再平衡</h3>
                  <p className="mb-3 text-sm text-gray-300">
                    您的资产配置过于集中在 SOL（85%），建议适当分散风险
                  </p>
                  <div className="flex items-center gap-3">
                    <Button size="sm">查看方案</Button>
                    <Button variant="outline" size="sm">
                      忽略
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
