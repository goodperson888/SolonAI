'use client'

import { useState } from 'react'
import { StatCard } from '@/components/dashboard/StatCard'
import { AssetCard } from '@/components/assets/AssetCard'
import { StrategyCard } from '@/components/strategy/StrategyCard'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { useTranslation } from '@/hooks/useTranslation'
import { mockAssets, mockPortfolioStats } from '@/data/mockAssets'
import { mockStrategies } from '@/data/mockStrategies'

type TabType = 'overview' | 'profit' | 'risk'

export default function DashboardPage() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<TabType>('overview')

  const tabs = [
    { id: 'overview' as TabType, name: '资产总览' },
    { id: 'profit' as TabType, name: '盈亏分析' },
    { id: 'risk' as TabType, name: '风险诊断' },
  ]

  return (
    <div className="min-h-screen bg-gray-950 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Page Title */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">{t('dashboard.title')}</h1>
          <p className="mt-2 text-gray-400">欢迎回来！这是你的资产概览</p>
        </div>

        {/* Stats Cards */}
        <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title={t('dashboard.totalValue')}
            value={`$${mockPortfolioStats.totalValue.toLocaleString()}`}
            change={mockPortfolioStats.change24h}
            trend={mockPortfolioStats.change24h >= 0 ? 'up' : 'down'}
            icon="💰"
          />
          <StatCard
            title={t('dashboard.todayProfit')}
            value={`$${mockPortfolioStats.changeValue.toLocaleString()}`}
            change={mockPortfolioStats.change24h}
            trend={mockPortfolioStats.change24h >= 0 ? 'up' : 'down'}
            icon="📈"
          />
          <StatCard
            title={t('dashboard.activeStrategies')}
            value={mockStrategies.filter((s) => s.deployed).length}
            icon="⚡"
          />
          <StatCard title={t('dashboard.riskLevel')} value={t('common.low')} icon="🛡️" />
        </div>

        {/* Tabs */}
        <div className="mb-8">
          <div className="border-b border-gray-800">
            <nav className="flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`border-b-2 px-1 py-4 text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'border-indigo-500 text-indigo-400'
                      : 'border-transparent text-gray-400 hover:border-gray-700 hover:text-gray-300'
                  }`}
                >
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Assets Section */}
            <div>
              <div className="mb-6 flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white">{t('dashboard.assets')}</h2>
                <button className="text-sm text-indigo-400 hover:text-indigo-300">
                  查看全部 →
                </button>
              </div>
              <div className="space-y-4">
                {mockAssets.map((asset) => (
                  <AssetCard key={asset.id} {...asset} />
                ))}
              </div>
            </div>

            {/* Active Strategies Section */}
            <div>
              <div className="mb-6 flex items-center justify-between">
                <h2 className="text-2xl font-bold text-white">活跃策略</h2>
                <button className="text-sm text-indigo-400 hover:text-indigo-300">
                  查看全部 →
                </button>
              </div>
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
                {mockStrategies
                  .filter((s) => s.deployed)
                  .map((strategy) => (
                    <StrategyCard key={strategy.id} {...strategy} />
                  ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'profit' && (
          <div className="space-y-8">
            {/* 盈亏概览 */}
            <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
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
                  <h3 className="text-lg font-semibold text-white">持仓盈亏</h3>
                  <span className="text-2xl">💎</span>
                </div>
                <p className="mb-2 text-3xl font-bold text-green-400">+$856.32</p>
                <p className="text-sm text-gray-400">浮动盈亏: +7.4%</p>
              </Card>

              <Card className="p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white">DeFi 收益</h3>
                  <span className="text-2xl">🌾</span>
                </div>
                <p className="mb-2 text-3xl font-bold text-green-400">+$124.56</p>
                <p className="text-sm text-gray-400">年化: 15.2%</p>
              </Card>
            </div>

            {/* 详细盈亏分析 */}
            <Card className="p-6">
              <h2 className="mb-6 text-xl font-bold text-white">盈亏明细</h2>
              <div className="space-y-4">
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

            {/* 收益优化建议 */}
            <Card className="p-6">
              <h2 className="mb-6 text-xl font-bold text-white">收益优化建议</h2>
              <div className="space-y-4">
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
              </div>
            </Card>
          </div>
        )}

        {activeTab === 'risk' && (
          <div className="space-y-8">
            {/* 风险概览 */}
            <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
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

            {/* 风险诊断 */}
            <Card className="p-6">
              <h2 className="mb-6 text-xl font-bold text-white">风险诊断</h2>
              <div className="space-y-4">
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">⚠️</span>
                    <div className="flex-1">
                      <div className="mb-2 flex items-center justify-between">
                        <h3 className="font-semibold text-white">检测到高危代币</h3>
                        <span className="rounded bg-red-500 px-2 py-1 text-xs text-white">
                          高风险
                        </span>
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

            {/* 授权管理 */}
            <Card className="p-6">
              <div className="mb-6 flex items-center justify-between">
                <h2 className="text-xl font-bold text-white">合约授权管理</h2>
                <Button variant="outline" size="sm">
                  一键撤销过期授权
                </Button>
              </div>

              <div className="space-y-4">
                <div className="rounded-lg border-l-4 border-red-500 bg-gray-800 p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="mb-2 flex items-center gap-3">
                        <h3 className="font-semibold text-white">Unknown DApp</h3>
                        <span className="rounded bg-red-500 px-2 py-1 text-xs text-white">
                          高危
                        </span>
                        <span className="rounded bg-gray-700 px-2 py-1 text-xs text-gray-300">
                          无限授权
                        </span>
                      </div>
                      <p className="mb-2 text-sm text-gray-400">合约地址: 7xKXt...9mPq</p>
                      <p className="text-sm text-yellow-400">
                        ⚠️ 该合约未通过审计，存在资产被盗风险
                      </p>
                    </div>
                    <Button variant="outline" size="sm" className="border-red-400 text-red-400">
                      立即撤销
                    </Button>
                  </div>
                </div>

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
                      <p className="text-sm text-gray-400">
                        授权时间: 2024-01-15 | 最后使用: 30天前
                      </p>
                    </div>
                    <Button variant="outline" size="sm">
                      撤销授权
                    </Button>
                  </div>
                </div>

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
                      <p className="text-sm text-gray-400">
                        授权额度: 100 USDC | 最后使用: 2小时前
                      </p>
                    </div>
                    <Button variant="ghost" size="sm">
                      管理
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
