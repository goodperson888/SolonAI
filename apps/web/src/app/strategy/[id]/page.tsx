'use client'

import { useParams } from 'next/navigation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ArrowLeft, TrendingUp, AlertTriangle, Clock, CheckCircle } from 'lucide-react'
import Link from 'next/link'

export default function StrategyDetailPage() {
  const params = useParams()
  const _strategyId = params.id

  return (
    <div className="min-h-screen bg-gray-950 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* 返回按钮 */}
        <Link
          href="/strategy"
          className="mb-6 inline-flex items-center text-gray-400 transition-colors hover:text-white"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          返回策略列表
        </Link>

        {/* 策略概览 */}
        <Card className="mb-8 p-6">
          <div className="mb-6 flex items-start justify-between">
            <div>
              <h1 className="mb-2 text-3xl font-bold text-white">SOL-USDC 流动性挖矿</h1>
              <p className="text-gray-400">通过 Raydium 提供流动性，赚取交易手续费和代币奖励</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-green-400">18.5%</div>
              <div className="text-sm text-gray-400">预期年化收益</div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
            <div>
              <div className="mb-1 text-sm text-gray-400">风险等级</div>
              <div className="flex items-center">
                <span className="rounded-full bg-yellow-500/20 px-3 py-1 text-sm text-yellow-400">
                  中等
                </span>
              </div>
            </div>
            <div>
              <div className="mb-1 text-sm text-gray-400">投入资金</div>
              <div className="text-lg font-semibold text-white">$10,000</div>
            </div>
            <div>
              <div className="mb-1 text-sm text-gray-400">预期日收益</div>
              <div className="text-lg font-semibold text-green-400">+$5.07</div>
            </div>
            <div>
              <div className="mb-1 text-sm text-gray-400">执行时间</div>
              <div className="text-lg font-semibold text-white">~30秒</div>
            </div>
          </div>
        </Card>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* 左侧：策略详情 */}
          <div className="space-y-8 lg:col-span-2">
            {/* 执行步骤 */}
            <Card className="p-6">
              <h2 className="mb-6 text-xl font-bold text-white">执行步骤</h2>
              <div className="space-y-4">
                <div className="flex items-start">
                  <div className="mr-4 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-indigo-600 font-semibold text-white">
                    1
                  </div>
                  <div className="flex-1">
                    <h3 className="mb-1 font-semibold text-white">准备资产</h3>
                    <p className="text-sm text-gray-400">将 $5,000 USDC 兑换为等值 SOL</p>
                    <div className="mt-2 text-xs text-gray-500">
                      预计 Gas: 0.00001 SOL (~$0.002)
                    </div>
                  </div>
                  <CheckCircle className="h-5 w-5 text-green-400" />
                </div>

                <div className="flex items-start">
                  <div className="mr-4 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-indigo-600 font-semibold text-white">
                    2
                  </div>
                  <div className="flex-1">
                    <h3 className="mb-1 font-semibold text-white">添加流动性</h3>
                    <p className="text-sm text-gray-400">在 Raydium 的 SOL-USDC 池中添加流动性</p>
                    <div className="mt-2 text-xs text-gray-500">
                      预计 Gas: 0.00005 SOL (~$0.009)
                    </div>
                  </div>
                  <div className="h-5 w-5 rounded-full border-2 border-gray-600" />
                </div>

                <div className="flex items-start">
                  <div className="mr-4 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gray-700 font-semibold text-white">
                    3
                  </div>
                  <div className="flex-1">
                    <h3 className="mb-1 font-semibold text-white">质押 LP Token</h3>
                    <p className="text-sm text-gray-400">将获得的 LP Token 质押到 Farm 合约</p>
                    <div className="mt-2 text-xs text-gray-500">
                      预计 Gas: 0.00003 SOL (~$0.006)
                    </div>
                  </div>
                  <div className="h-5 w-5 rounded-full border-2 border-gray-600" />
                </div>
              </div>

              <div className="mt-6 border-t border-gray-800 pt-6">
                <Button variant="primary" size="lg" className="w-full">
                  一键执行策略
                </Button>
              </div>
            </Card>

            {/* 收益分析 */}
            <Card className="p-6">
              <h2 className="mb-6 text-xl font-bold text-white">收益分析</h2>
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-gray-800 py-3">
                  <span className="text-gray-400">交易手续费收益</span>
                  <span className="font-semibold text-white">12.3% APY</span>
                </div>
                <div className="flex items-center justify-between border-b border-gray-800 py-3">
                  <span className="text-gray-400">RAY 代币奖励</span>
                  <span className="font-semibold text-white">6.2% APY</span>
                </div>
                <div className="flex items-center justify-between py-3">
                  <span className="font-semibold text-gray-400">总预期收益</span>
                  <span className="text-lg font-bold text-green-400">18.5% APY</span>
                </div>
              </div>

              <div className="mt-6 rounded-lg border border-blue-500/30 bg-blue-500/10 p-4">
                <div className="flex items-start">
                  <TrendingUp className="mr-3 mt-0.5 h-5 w-5 text-blue-400" />
                  <div>
                    <h3 className="mb-1 font-semibold text-blue-400">收益预测</h3>
                    <p className="text-sm text-gray-300">
                      投入 $10,000，预计 30 天后可获得约 $151.23 收益
                    </p>
                  </div>
                </div>
              </div>
            </Card>

            {/* 风险提示 */}
            <Card className="p-6">
              <h2 className="mb-6 text-xl font-bold text-white">风险提示</h2>
              <div className="space-y-4">
                <div className="flex items-start rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-4">
                  <AlertTriangle className="mr-3 mt-0.5 h-5 w-5 flex-shrink-0 text-yellow-400" />
                  <div>
                    <h3 className="mb-1 font-semibold text-yellow-400">无常损失风险</h3>
                    <p className="text-sm text-gray-300">
                      当 SOL 和 USDC 价格比例变化时，可能产生无常损失。建议在价格相对稳定时参与。
                    </p>
                  </div>
                </div>

                <div className="flex items-start rounded-lg border border-yellow-500/30 bg-yellow-500/10 p-4">
                  <AlertTriangle className="mr-3 mt-0.5 h-5 w-5 flex-shrink-0 text-yellow-400" />
                  <div>
                    <h3 className="mb-1 font-semibold text-yellow-400">智能合约风险</h3>
                    <p className="text-sm text-gray-300">
                      Raydium 已通过多次审计，但仍存在智能合约漏洞风险。建议分散投资。
                    </p>
                  </div>
                </div>

                <div className="flex items-start rounded-lg border border-blue-500/30 bg-blue-500/10 p-4">
                  <Clock className="mr-3 mt-0.5 h-5 w-5 flex-shrink-0 text-blue-400" />
                  <div>
                    <h3 className="mb-1 font-semibold text-blue-400">流动性锁定</h3>
                    <p className="text-sm text-gray-300">
                      资金可随时提取，但频繁进出会增加 Gas 成本。建议至少持有 7 天以上。
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* 右侧：监控面板 */}
          <div className="space-y-8">
            {/* 实时数据 */}
            <Card className="p-6">
              <h2 className="mb-4 text-lg font-bold text-white">实时数据</h2>
              <div className="space-y-4">
                <div>
                  <div className="mb-1 text-sm text-gray-400">池子 TVL</div>
                  <div className="text-xl font-bold text-white">$125.6M</div>
                  <div className="text-xs text-green-400">+2.3% 24h</div>
                </div>
                <div>
                  <div className="mb-1 text-sm text-gray-400">24h 交易量</div>
                  <div className="text-xl font-bold text-white">$8.2M</div>
                  <div className="text-xs text-green-400">+5.7% 24h</div>
                </div>
                <div>
                  <div className="mb-1 text-sm text-gray-400">当前 APY</div>
                  <div className="text-xl font-bold text-green-400">18.5%</div>
                  <div className="text-xs text-gray-400">7日平均: 17.8%</div>
                </div>
              </div>
            </Card>

            {/* 协议信息 */}
            <Card className="p-6">
              <h2 className="mb-4 text-lg font-bold text-white">协议信息</h2>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">协议</span>
                  <span className="text-sm font-semibold text-white">Raydium</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">审计状态</span>
                  <span className="text-sm text-green-400">✓ 已审计</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">TVL 排名</span>
                  <span className="text-sm text-white">#3 on Solana</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">运行时间</span>
                  <span className="text-sm text-white">2+ 年</span>
                </div>
              </div>
            </Card>

            {/* 历史表现 */}
            <Card className="p-6">
              <h2 className="mb-4 text-lg font-bold text-white">历史表现</h2>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">7日 APY</span>
                  <span className="text-sm text-white">17.8%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">30日 APY</span>
                  <span className="text-sm text-white">19.2%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">最高 APY</span>
                  <span className="text-sm text-green-400">28.5%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">最低 APY</span>
                  <span className="text-sm text-red-400">12.3%</span>
                </div>
              </div>
            </Card>

            {/* 相似策略 */}
            <Card className="p-6">
              <h2 className="mb-4 text-lg font-bold text-white">相似策略</h2>
              <div className="space-y-3">
                <Link
                  href="/strategy/2"
                  className="block rounded-lg bg-gray-800/50 p-3 transition-colors hover:bg-gray-800"
                >
                  <div className="mb-1 text-sm font-semibold text-white">SOL-RAY 流动性</div>
                  <div className="text-xs text-gray-400">APY: 22.3%</div>
                </Link>
                <Link
                  href="/strategy/3"
                  className="block rounded-lg bg-gray-800/50 p-3 transition-colors hover:bg-gray-800"
                >
                  <div className="mb-1 text-sm font-semibold text-white">USDC-USDT 稳定币</div>
                  <div className="text-xs text-gray-400">APY: 8.5%</div>
                </Link>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
