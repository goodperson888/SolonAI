export interface Asset {
  symbol: string
  balance: number
  valueUsd: number
  change24h: number
  color?: string
}

export interface PnLRecord {
  date: string
  profitUsd: number
  roi: number
}

export interface RiskDiagnosis {
  healthScore: number
  dimensions: { category: string; score: number }[]
  warnings: string[]
  aiAdvice: string
}
