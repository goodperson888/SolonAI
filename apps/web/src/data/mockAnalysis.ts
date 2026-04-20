import { Asset, PnLRecord, RiskDiagnosis } from '@/types/analysis'

export const mockAssets: Asset[] = [
  { symbol: 'SOL', balance: 50.5, valueUsd: 7500.5, change24h: 5.2, color: '#14F195' },
  { symbol: 'USDC', balance: 3500, valueUsd: 3500, change24h: 0.01, color: '#2775CA' },
  { symbol: 'BONK', balance: 150000, valueUsd: 1200.3, change24h: -2.5, color: '#F38120' },
  { symbol: 'JUP', balance: 25000, valueUsd: 257.5, change24h: 12.4, color: '#00C49F' },
]

export const mockPnLData: PnLRecord[] = [
  { date: '2023-10-01', profitUsd: 100, roi: 1.5 },
  { date: '2023-10-05', profitUsd: 250, roi: 3.2 },
  { date: '2023-10-10', profitUsd: 180, roi: 2.1 },
  { date: '2023-10-15', profitUsd: 400, roi: 5.5 },
  { date: '2023-10-20', profitUsd: 350, roi: 4.8 },
  { date: '2023-10-25', profitUsd: 650, roi: 8.2 },
  { date: '2023-10-30', profitUsd: 856.32, roi: 10.5 },
]

export const mockRiskDiagnosis: RiskDiagnosis = {
  healthScore: 78,
  dimensions: [
    { category: '波动率', score: 65 },
    { category: '流动性', score: 90 },
    { category: '集中度', score: 55 },
    { category: '合约安全', score: 85 },
    { category: '杠杆风险', score: 95 },
  ],
  warnings: [
    '您持有的 SCAM 代币存在较高 Rug Pull 风险，建议立即清仓。',
    'SOL 资产集中度超过 60%，建议适当分散配置。',
    '3个过期合约拥有您的无限授权，请及时撤销。',
  ],
  aiAdvice:
    '综合您的链上数据，当前资产组合处于中低风险水平。流动性储备充足，未发现过度杠杆行为。但您的 SOL 持仓过于集中，同时检测到部分无价值的土狗币授权，这可能会暴露于钓鱼风险中。建议将部分闲置 USDC 存入 MarginFi 以获取稳定收益，并立刻清理不明合约授权。',
}
