'use client'

import { useState, useEffect } from 'react'
import { useTranslation } from '@/hooks/useTranslation'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { useWallet } from '@solana/wallet-adapter-react'
import {
  riskApi,
  type RiskAssessment,
  type Transaction,
  type RiskAlert,
  type Authorization,
} from '@/lib/api-client'

type TabType = 'overview' | 'authorizations' | 'alerts' | 'transactions'

export default function RiskControlPage() {
  const { t: _t } = useTranslation()
  const { publicKey } = useWallet()
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [assessment, setAssessment] = useState<RiskAssessment | null>(null)
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [alerts, setAlerts] = useState<RiskAlert[]>([])
  const [authorizations, setAuthorizations] = useState<Authorization[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (publicKey) {
      loadData()
    }
  }, [publicKey, activeTab])

  const loadData = async () => {
    if (!publicKey) return

    setLoading(true)
    try {
      const walletAddress = publicKey.toBase58()

      if (activeTab === 'overview') {
        const [assessmentData, transactionsData] = await Promise.all([
          riskApi.assessment(walletAddress),
          riskApi.transactions(walletAddress, 10),
        ])
        setAssessment(assessmentData)
        setTransactions(transactionsData.transactions || [])
      } else if (activeTab === 'transactions') {
        const data = await riskApi.transactions(walletAddress, 50)
        setTransactions(data.transactions || [])
      } else if (activeTab === 'alerts') {
        const data = await riskApi.alerts(walletAddress)
        setAlerts(data.alerts || [])
      } else if (activeTab === 'authorizations') {
        const data = await riskApi.authorizations(walletAddress)
        setAuthorizations(data.authorizations || [])
      }
    } catch (error) {
      console.error('Failed to load risk data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRevokeAuth = async (authId: string) => {
    if (!publicKey) return

    try {
      await riskApi.revokeAuth(authId, publicKey.toBase58())
      // 重新加载授权列表
      await loadData()
    } catch (error) {
      console.error('Failed to revoke authorization:', error)
    }
  }

  const tabs = [
    { id: 'overview' as TabType, name: '风险概览' },
    { id: 'authorizations' as TabType, name: '授权管理' },
    { id: 'alerts' as TabType, name: '钓鱼检测' },
    { id: 'transactions' as TabType, name: '交易历史' },
  ]

  const getRiskLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'low':
        return 'text-green-400'
      case 'medium':
        return 'text-yellow-400'
      case 'high':
      case 'critical':
        return 'text-red-400'
      default:
        return 'text-gray-400'
    }
  }

  const getRiskLevelBg = (level: string) => {
    switch (level.toLowerCase()) {
      case 'low':
        return 'bg-green-500/20 text-green-400'
      case 'medium':
        return 'bg-yellow-500/20 text-yellow-400'
      case 'high':
      case 'critical':
        return 'bg-red-500/20 text-red-400'
      default:
        return 'bg-gray-500/20 text-gray-400'
    }
  }

  if (!publicKey) {
    return (
      <div className="min-h-screen bg-gray-950 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center text-gray-400">请先连接钱包</div>
        </div>
      </div>
    )
  }

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

        {loading && <div className="text-center text-gray-400">加载中...</div>}

        {/* Tab Content */}
        {!loading && activeTab === 'overview' && assessment && (
          <>
            {/* 风险概览 */}
            <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-4">
              <Card className="p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-400">风险评分</h3>
                  <span className="text-2xl">🔍</span>
                </div>
                <p className={`text-3xl font-bold ${getRiskLevelColor(assessment.risk_level)}`}>
                  {assessment.overall_risk_score}
                </p>
              </Card>

              <Card className="p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-400">风险等级</h3>
                  <span className="text-2xl">⚠️</span>
                </div>
                <p
                  className={`text-2xl font-bold capitalize ${getRiskLevelColor(assessment.risk_level)}`}
                >
                  {assessment.risk_level}
                </p>
              </Card>

              <Card className="p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-400">风险因素</h3>
                  <span className="text-2xl">⚡</span>
                </div>
                <p className="text-3xl font-bold text-yellow-400">
                  {assessment.risk_factors.length}
                </p>
              </Card>

              <Card className="p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-sm font-medium text-gray-400">建议数</h3>
                  <span className="text-2xl">ℹ️</span>
                </div>
                <p className="text-3xl font-bold text-blue-400">
                  {assessment.recommendations.length}
                </p>
              </Card>
            </div>

            {/* 风险因素 */}
            <Card className="mb-8 p-6">
              <h2 className="mb-6 text-xl font-bold text-white">风险因素</h2>
              <div className="space-y-4">
                {assessment.risk_factors.map((factor, index) => (
                  <div key={index} className="rounded-lg bg-gray-800 p-4">
                    <div className="mb-2 flex items-center justify-between">
                      <h3 className="font-semibold text-white">{factor.factor}</h3>
                      <span
                        className={`rounded px-2 py-1 text-xs ${getRiskLevelBg(factor.impact)}`}
                      >
                        {factor.impact}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400">{factor.description}</p>
                    <p className="mt-2 text-sm text-gray-500">评分: {factor.score}</p>
                  </div>
                ))}
              </div>
            </Card>

            {/* 实时交易监控 */}
            <Card className="p-6">
              <h2 className="mb-6 text-xl font-bold text-white">最近交易</h2>
              <div className="space-y-4">
                {transactions.slice(0, 5).map((tx, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between rounded-lg bg-gray-800 p-4"
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={`flex h-12 w-12 items-center justify-center rounded-full ${
                          tx.status === 'success' ? 'bg-green-500/20' : 'bg-red-500/20'
                        }`}
                      >
                        <span className="text-2xl">{tx.status === 'success' ? '✅' : '❌'}</span>
                      </div>
                      <div>
                        <p className="font-medium text-white">{tx.type}</p>
                        <p className="text-sm text-gray-400">
                          {tx.amount && tx.token
                            ? `${tx.amount} ${tx.token}`
                            : tx.signature?.slice(0, 8)}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-400">
                        {new Date(tx.timestamp).toLocaleString('zh-CN')}
                      </p>
                      <span
                        className={`text-xs ${getRiskLevelBg(tx.risk_score ? 'medium' : 'low')}`}
                      >
                        风险: {tx.risk_score || 'N/A'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </>
        )}

        {!loading && activeTab === 'authorizations' && (
          <Card className="p-6">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-xl font-bold text-white">合约授权管理</h2>
            </div>

            <div className="space-y-4">
              {authorizations.length === 0 ? (
                <div className="text-center text-gray-400">暂无授权记录</div>
              ) : (
                authorizations.map((auth) => (
                  <div
                    key={auth.id}
                    className={`rounded-lg border-l-4 bg-gray-800 p-4 ${
                      auth.risk_level === 'high'
                        ? 'border-red-500'
                        : auth.risk_level === 'medium'
                          ? 'border-yellow-500'
                          : 'border-green-500'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="mb-2 flex items-center gap-3">
                          <h3 className="font-semibold text-white">{auth.program_name}</h3>
                          <span
                            className={`rounded px-2 py-1 text-xs ${getRiskLevelBg(auth.risk_level)}`}
                          >
                            {auth.risk_level}
                          </span>
                        </div>
                        <p className="mb-2 text-sm text-gray-400">合约: {auth.program_id}</p>
                        <p className="text-sm text-gray-400">
                          授权时间: {new Date(auth.granted_at).toLocaleString('zh-CN')}
                          {auth.last_used &&
                            ` | 最后使用: ${new Date(auth.last_used).toLocaleString('zh-CN')}`}
                        </p>
                        <p className="mt-2 text-xs text-gray-500">
                          权限: {auth.permissions.join(', ')}
                        </p>
                      </div>
                      <div className="flex flex-col gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          className={
                            auth.risk_level === 'high' ? 'border-red-400 text-red-400' : ''
                          }
                          onClick={() => handleRevokeAuth(auth.id)}
                        >
                          撤销授权
                        </Button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        )}

        {!loading && activeTab === 'alerts' && (
          <Card className="p-6">
            <h2 className="mb-6 text-xl font-bold text-white">风险预警</h2>

            <div className="space-y-4">
              {alerts.length === 0 ? (
                <div className="text-center text-gray-400">暂无预警</div>
              ) : (
                alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`rounded-lg border p-4 ${
                      alert.severity === 'critical' || alert.severity === 'high'
                        ? 'border-red-500/30 bg-red-500/10'
                        : 'border-yellow-500/30 bg-yellow-500/10'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">
                        {alert.severity === 'critical' || alert.severity === 'high' ? '🚨' : '⚠️'}
                      </span>
                      <div className="flex-1">
                        <div className="mb-2 flex items-center justify-between">
                          <h3 className="font-semibold text-white">{alert.title}</h3>
                          <span className="text-sm text-gray-400">
                            {new Date(alert.created_at).toLocaleString('zh-CN')}
                          </span>
                        </div>
                        <p className="mb-2 text-sm text-gray-300">{alert.description}</p>
                        <div className="flex items-center gap-2">
                          <span
                            className={`rounded px-2 py-1 text-xs ${getRiskLevelBg(alert.severity)}`}
                          >
                            {alert.severity}
                          </span>
                          <span className="text-xs text-gray-400">{alert.alert_type}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        )}

        {!loading && activeTab === 'transactions' && (
          <>
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
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {transactions.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-6 py-8 text-center text-gray-400">
                          暂无交易记录
                        </td>
                      </tr>
                    ) : (
                      transactions.map((tx, index) => (
                        <tr key={index} className="transition-colors hover:bg-gray-800/50">
                          <td className="px-6 py-4">
                            <div>
                              <p className="text-sm text-white">
                                {new Date(tx.timestamp).toLocaleDateString('zh-CN')}
                              </p>
                              <p className="text-xs text-gray-400">
                                {new Date(tx.timestamp).toLocaleTimeString('zh-CN')}
                              </p>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className="rounded-full bg-blue-500/20 px-3 py-1 text-xs text-blue-400">
                              {tx.type}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <div>
                              <p className="text-sm text-white">
                                {tx.from && tx.to
                                  ? `${tx.from.slice(0, 6)}...${tx.from.slice(-4)} → ${tx.to.slice(0, 6)}...${tx.to.slice(-4)}`
                                  : tx.signature?.slice(0, 16)}
                              </p>
                              {tx.token && <p className="text-xs text-gray-400">{tx.token}</p>}
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <p className="text-sm text-white">{tx.amount || 'N/A'}</p>
                          </td>
                          <td className="px-6 py-4">
                            <span
                              className={`rounded-full px-3 py-1 text-xs ${
                                tx.status === 'success'
                                  ? 'bg-green-500/20 text-green-400'
                                  : tx.status === 'failed'
                                    ? 'bg-red-500/20 text-red-400'
                                    : 'bg-yellow-500/20 text-yellow-400'
                              }`}
                            >
                              {tx.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </Card>
          </>
        )}
      </div>
    </div>
  )
}
