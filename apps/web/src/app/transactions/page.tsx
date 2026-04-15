'use client'

import { useTranslation } from '@/hooks/useTranslation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'

export default function TransactionsPage() {
  const { t: _t } = useTranslation()

  return (
    <div className="min-h-screen bg-gray-950 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">交易历史</h1>
          <p className="mt-2 text-gray-400">查看您的所有链上交易记录</p>
        </div>

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
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">时间</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">类型</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">详情</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">金额</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">状态</th>
                  <th className="px-6 py-4 text-left text-sm font-semibold text-gray-300">操作</th>
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
      </div>
    </div>
  )
}
