'use client'

import { useState } from 'react'
import { useTranslation } from '@/hooks/useTranslation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'

type TabType = 'overview' | 'authorizations' | 'alerts' | 'transactions'

export default function RiskControlPage() {
  const { t: _t } = useTranslation()
  const [activeTab, setActiveTab] = useState<TabType>('overview')

  const tabs = [
    { id: 'overview' as TabType, name: '风险概览' },
    { id: 'authorizations' as TabType, name: '授权管理' },
    { id: 'alerts' as TabType, name: '钓鱼检测' },
    { id: 'transactions' as TabType, name: '交易历史' },
  ]

  return (
    <div className="min-h-screen bg-gray-950 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">风控审计中心</h1>
          <p className="mt-2 text-gray-400">全方位保护您的链上资产安全</p>
        </div>

        {/* Tab Navigation */}
        <div className="mb-8 flex space-x-4 border-b border-gray-800">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-4 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'border-b-2 border-indigo-500 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab.name}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <>
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

            {/* 实时交易监控 */}
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
          </>
        )}

        {activeTab === 'authorizations' && (
          <Card className="p-6">
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
                      <span className="rounded bg-yellow-500 px-2 py-1 text-xs text-white">
                        中危
                      </span>
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
                      <span className="rounded bg-green-500 px-2 py-1 text-xs text-white">
                        安全
                      </span>
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
        )}

        {activeTab === 'alerts' && (
          <Card className="p-6">
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
        )}

        {activeTab === 'transactions' && (
          <>
            {/* 筛选器 */}
            <Card className="mb-8 p-6">
              <div className="flex flex-wrap items-center gap-4">
                <select className="rounded-lg border border-gray-700 bg-gray-800 px-4 py-2 text-white focus:border-primary-500 focus:outline-none">
                  <option>全部类型</option>
                  <option>Swap</option>
                  <option>转账</option>
                  <option>DeFi操作</option>
                  <option>NFT交易</option>
                </select>

                <select className="rounded-lg border border-gray-700 bg-gray-800 px-4 py-2 text-white focus:border-primary-500 focus:outline-none">
                  <option>全部状态</option>
                  <option>成功</option>
                  <option>失败</option>
                  <option>待确认</option>
                </select>

                <select className="rounded-lg border border-gray-700 bg-gray-800 px-4 py-2 text-white focus:border-primary-500 focus:outline-none">
                  <option>最近7天</option>
                  <option>最近30天</option>
                  <option>最近90天</option>
                  <option>全部时间</option>
                </select>

                <Button variant="outline" size="sm">
                  导出CSV
                </Button>
              </div>
            </Card>

            {/* 交易列表 */}
            <Card className="overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-800">
                    <tr>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                        时间
                      </th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                        类型
                      </th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                        详情
                      </th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                        金额
                      </th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                        状态
                      </th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">
                        操作
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {/* 交易1 */}
                    <tr className="transition-colors hover:bg-gray-800/50">
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm text-white">2024-04-15</p>
                          <p className="text-xs text-gray-400">14:32:18</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="rounded-full bg-blue-500/20 px-3 py-1 text-xs text-blue-400">
                          Swap
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm text-white">10 SOL → 1,850 USDC</p>
                          <p className="text-xs text-gray-400">通过 Jupiter</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-sm text-white">$1,850.00</p>
                      </td>
                      <td className="px-6 py-4">
                        <span className="rounded-full bg-green-500/20 px-3 py-1 text-xs text-green-400">
                          成功
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <Button variant="ghost" size="sm">
                          查看
                        </Button>
                      </td>
                    </tr>

                    {/* 交易2 */}
                    <tr className="transition-colors hover:bg-gray-800/50">
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm text-white">2024-04-15</p>
                          <p className="text-xs text-gray-400">12:15:42</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="rounded-full bg-purple-500/20 px-3 py-1 text-xs text-purple-400">
                          DeFi
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm text-white">存入 MarginFi</p>
                          <p className="text-xs text-gray-400">50 SOL 借贷生息</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-sm text-white">$9,250.00</p>
                      </td>
                      <td className="px-6 py-4">
                        <span className="rounded-full bg-green-500/20 px-3 py-1 text-xs text-green-400">
                          成功
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <Button variant="ghost" size="sm">
                          查看
                        </Button>
                      </td>
                    </tr>

                    {/* 交易3 */}
                    <tr className="transition-colors hover:bg-gray-800/50">
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm text-white">2024-04-14</p>
                          <p className="text-xs text-gray-400">18:45:23</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="rounded-full bg-green-500/20 px-3 py-1 text-xs text-green-400">
                          转账
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm text-white">接收 100 USDC</p>
                          <p className="text-xs text-gray-400">来自 7xKXt...9mPq</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-sm text-green-400">+$100.00</p>
                      </td>
                      <td className="px-6 py-4">
                        <span className="rounded-full bg-green-500/20 px-3 py-1 text-xs text-green-400">
                          成功
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <Button variant="ghost" size="sm">
                          查看
                        </Button>
                      </td>
                    </tr>

                    {/* 交易4 */}
                    <tr className="transition-colors hover:bg-gray-800/50">
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm text-white">2024-04-14</p>
                          <p className="text-xs text-gray-400">16:22:11</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="rounded-full bg-purple-500/20 px-3 py-1 text-xs text-purple-400">
                          DeFi
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm text-white">添加流动性</p>
                          <p className="text-xs text-gray-400">SOL-USDC Pool @ Raydium</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-sm text-white">$5,000.00</p>
                      </td>
                      <td className="px-6 py-4">
                        <span className="rounded-full bg-green-500/20 px-3 py-1 text-xs text-green-400">
                          成功
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <Button variant="ghost" size="sm">
                          查看
                        </Button>
                      </td>
                    </tr>

                    {/* 交易5 - 失败 */}
                    <tr className="transition-colors hover:bg-gray-800/50">
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm text-white">2024-04-13</p>
                          <p className="text-xs text-gray-400">20:10:55</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="rounded-full bg-blue-500/20 px-3 py-1 text-xs text-blue-400">
                          Swap
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm text-white">5 SOL → RAY</p>
                          <p className="text-xs text-gray-400">通过 Raydium</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-sm text-white">$925.00</p>
                      </td>
                      <td className="px-6 py-4">
                        <span className="rounded-full bg-red-500/20 px-3 py-1 text-xs text-red-400">
                          失败
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <Button variant="ghost" size="sm">
                          查看
                        </Button>
                      </td>
                    </tr>

                    {/* 交易6 */}
                    <tr className="transition-colors hover:bg-gray-800/50">
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm text-white">2024-04-13</p>
                          <p className="text-xs text-gray-400">15:30:42</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="rounded-full bg-yellow-500/20 px-3 py-1 text-xs text-yellow-400">
                          NFT
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm text-white">购买 NFT</p>
                          <p className="text-xs text-gray-400">Mad Lads #1234</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <p className="text-sm text-white">15 SOL</p>
                      </td>
                      <td className="px-6 py-4">
                        <span className="rounded-full bg-green-500/20 px-3 py-1 text-xs text-green-400">
                          成功
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <Button variant="ghost" size="sm">
                          查看
                        </Button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* 分页 */}
              <div className="flex items-center justify-between border-t border-gray-800 px-6 py-4">
                <p className="text-sm text-gray-400">显示 1-6 条，共 156 条记录</p>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" disabled>
                    上一页
                  </Button>
                  <Button variant="outline" size="sm">
                    1
                  </Button>
                  <Button variant="ghost" size="sm">
                    2
                  </Button>
                  <Button variant="ghost" size="sm">
                    3
                  </Button>
                  <Button variant="outline" size="sm">
                    下一页
                  </Button>
                </div>
              </div>
            </Card>
          </>
        )}
      </div>
    </div>
  )
}
