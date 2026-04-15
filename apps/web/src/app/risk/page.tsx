'use client'

import { useTranslation } from '@/hooks/useTranslation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'

export default function RiskControlPage() {
  const { t: _t } = useTranslation()

  return (
    <div className="min-h-screen bg-gray-950 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">风控审计中心</h1>
          <p className="mt-2 text-gray-400">全方位保护您的链上资产安全</p>
        </div>

        {/* 风险概览 */}
        <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-4">
          <Card className="p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-400">总风险项</h3>
              <span className="text-2xl">🔍</span>
            </div>
            <p className="text-3xl font-bold text-white">5</p>
          </Card>

          <Card className="p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-400">高危风险</h3>
              <span className="text-2xl">⚠️</span>
            </div>
            <p className="text-3xl font-bold text-red-400">1</p>
          </Card>

          <Card className="p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-400">中等风险</h3>
              <span className="text-2xl">⚡</span>
            </div>
            <p className="text-3xl font-bold text-yellow-400">3</p>
          </Card>

          <Card className="p-6">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-400">低风险</h3>
              <span className="text-2xl">ℹ️</span>
            </div>
            <p className="text-3xl font-bold text-blue-400">1</p>
          </Card>
        </div>

        {/* 授权管理 */}
        <Card className="mb-8 p-6">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-xl font-bold text-white">合约授权管理</h2>
            <Button variant="outline" size="sm">
              一键撤销过期授权
            </Button>
          </div>

          <div className="space-y-4">
            {/* 授权项1 - 高危 */}
            <div className="rounded-lg border-l-4 border-red-500 bg-gray-800 p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="mb-2 flex items-center gap-3">
                    <h3 className="font-semibold text-white">Unknown DApp</h3>
                    <span className="rounded bg-red-500 px-2 py-1 text-xs text-white">高危</span>
                    <span className="rounded bg-gray-700 px-2 py-1 text-xs text-gray-300">
                      无限授权
                    </span>
                  </div>
                  <p className="mb-2 text-sm text-gray-400">合约地址: 7xKXt...9mPq</p>
                  <p className="text-sm text-yellow-400">⚠️ 该合约未通过审计，存在资产被盗风险</p>
                </div>
                <div className="flex flex-col gap-2">
                  <Button variant="outline" size="sm" className="border-red-400 text-red-400">
                    立即撤销
                  </Button>
                  <Button variant="ghost" size="sm">
                    详情
                  </Button>
                </div>
              </div>
            </div>

            {/* 授权项2 - 中危 */}
            <div className="rounded-lg border-l-4 border-yellow-500 bg-gray-800 p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="mb-2 flex items-center gap-3">
                    <h3 className="font-semibold text-white">Raydium V3</h3>
                    <span className="rounded bg-yellow-500 px-2 py-1 text-xs text-white">中危</span>
                    <span className="rounded bg-gray-700 px-2 py-1 text-xs text-gray-300">
                      无限授权
                    </span>
                  </div>
                  <p className="mb-2 text-sm text-gray-400">合约地址: CAMMCzo...5xfM</p>
                  <p className="text-sm text-gray-400">授权时间: 2024-01-15 | 最后使用: 30天前</p>
                </div>
                <div className="flex flex-col gap-2">
                  <Button variant="outline" size="sm">
                    撤销授权
                  </Button>
                  <Button variant="ghost" size="sm">
                    详情
                  </Button>
                </div>
              </div>
            </div>

            {/* 授权项3 - 正常 */}
            <div className="rounded-lg border-l-4 border-green-500 bg-gray-800 p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="mb-2 flex items-center gap-3">
                    <h3 className="font-semibold text-white">Jupiter Aggregator</h3>
                    <span className="rounded bg-green-500 px-2 py-1 text-xs text-white">安全</span>
                    <span className="rounded bg-gray-700 px-2 py-1 text-xs text-gray-300">
                      限额授权
                    </span>
                  </div>
                  <p className="mb-2 text-sm text-gray-400">合约地址: JUP4Fb2...cKzZ</p>
                  <p className="text-sm text-gray-400">授权额度: 100 USDC | 最后使用: 2小时前</p>
                </div>
                <div className="flex flex-col gap-2">
                  <Button variant="ghost" size="sm">
                    管理
                  </Button>
                  <Button variant="ghost" size="sm">
                    详情
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* 钓鱼检测 */}
        <Card className="mb-8 p-6">
          <h2 className="mb-6 text-xl font-bold text-white">钓鱼合约检测</h2>

          <div className="space-y-4">
            {/* 检测记录1 */}
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">🚨</span>
                <div className="flex-1">
                  <div className="mb-2 flex items-center justify-between">
                    <h3 className="font-semibold text-white">拦截钓鱼交易</h3>
                    <span className="text-sm text-gray-400">2小时前</span>
                  </div>
                  <p className="mb-2 text-sm text-gray-300">
                    检测到您尝试与已知钓鱼合约交互，已自动拦截
                  </p>
                  <p className="font-mono text-xs text-gray-400">合约: ScamXXX...fake</p>
                </div>
              </div>
            </div>

            {/* 检测记录2 */}
            <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-4">
              <div className="flex items-start gap-3">
                <span className="text-2xl">⚠️</span>
                <div className="flex-1">
                  <div className="mb-2 flex items-center justify-between">
                    <h3 className="font-semibold text-white">可疑代币警告</h3>
                    <span className="text-sm text-gray-400">1天前</span>
                  </div>
                  <p className="mb-2 text-sm text-gray-300">
                    检测到您持有的 MEME 代币存在异常交易模式
                  </p>
                  <Button variant="outline" size="sm">
                    查看详情
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* 交易监控 */}
        <Card className="p-6">
          <h2 className="mb-6 text-xl font-bold text-white">实时交易监控</h2>

          <div className="space-y-4">
            {/* 监控项1 */}
            <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-500/20">
                  <span className="text-2xl">✅</span>
                </div>
                <div>
                  <p className="font-medium text-white">Swap: 10 SOL → 1,850 USDC</p>
                  <p className="text-sm text-gray-400">通过 Jupiter | 风险评级: 低</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400">5分钟前</p>
                <Button variant="ghost" size="sm">
                  详情
                </Button>
              </div>
            </div>

            {/* 监控项2 */}
            <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-500/20">
                  <span className="text-2xl">✅</span>
                </div>
                <div>
                  <p className="font-medium text-white">存入 MarginFi: 50 SOL</p>
                  <p className="text-sm text-gray-400">借贷协议 | 风险评级: 低</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400">1小时前</p>
                <Button variant="ghost" size="sm">
                  详情
                </Button>
              </div>
            </div>

            {/* 监控项3 */}
            <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
              <div className="flex items-center gap-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-yellow-500/20">
                  <span className="text-2xl">⚠️</span>
                </div>
                <div>
                  <p className="font-medium text-white">授权: Unknown DApp</p>
                  <p className="text-sm text-yellow-400">未审计合约 | 风险评级: 高</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400">2天前</p>
                <Button variant="ghost" size="sm">
                  详情
                </Button>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
