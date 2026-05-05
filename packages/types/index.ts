/**
 * 用户相关类型定义
 */

export interface User {
  id: string;
  wallet_address: string;
  email?: string;
  created_at: string;
  updated_at: string;
}

export interface UserPreferences {
  risk_level: 'conservative' | 'balanced' | 'aggressive';
  notification_enabled: boolean;
  language: 'zh-CN' | 'en-US';
}

/**
 * 资产相关类型定义
 */

export interface TokenBalance {
  mint: string;
  symbol: string;
  name: string;
  balance: number;
  decimals: number;
  usd_value: number;
  logo_uri?: string;
}

export interface AssetSummary {
  total_value_usd: number;
  sol_balance: number;
  token_count: number;
  tokens: TokenBalance[];
}

/**
 * DeFi策略相关类型定义
 */

export interface Strategy {
  id: string;
  user_id: string;
  type: 'swap' | 'lending' | 'staking' | 'liquidity';
  status: 'pending' | 'approved' | 'executing' | 'completed' | 'failed';
  input_tokens: TokenAmount[];
  output_tokens: TokenAmount[];
  estimated_apy?: number;
  risk_score: number;
  created_at: string;
  executed_at?: string;
}

export interface TokenAmount {
  mint: string;
  symbol: string;
  amount: number;
  usd_value: number;
}

export interface StrategyRecommendation {
  strategy_type: string;
  description: string;
  estimated_return: number;
  risk_level: 'low' | 'medium' | 'high';
  protocols: string[];
  steps: StrategyStep[];
}

export interface StrategyStep {
  order: number;
  action: string;
  protocol: string;
  params: Record<string, any>;
}

/**
 * 交易相关类型定义
 */

export interface Transaction {
  id: string;
  signature: string;
  user_id: string;
  strategy_id?: string;
  type: 'swap' | 'deposit' | 'borrow' | 'withdraw' | 'repay';
  status: 'pending' | 'confirmed' | 'failed';
  amount: number;
  token_mint: string;
  created_at: string;
  confirmed_at?: string;
}

export interface TransactionInstruction {
  program_id: string;
  accounts: AccountMeta[];
  data: string;
}

export interface AccountMeta {
  pubkey: string;
  is_signer: boolean;
  is_writable: boolean;
}

/**
 * AI智能体相关类型定义
 */

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface IntentAnalysis {
  intent_type: 'query' | 'swap' | 'lend' | 'borrow' | 'stake' | 'unknown';
  confidence: number;
  entities: Record<string, any>;
  suggested_actions: string[];
}

export interface RiskAssessment {
  overall_risk: 'low' | 'medium' | 'high' | 'critical';
  risk_factors: RiskFactor[];
  warnings: string[];
  is_approved: boolean;
}

export interface RiskFactor {
  category: 'token' | 'protocol' | 'market' | 'user';
  severity: 'low' | 'medium' | 'high';
  description: string;
}

/**
 * API响应类型定义
 */

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: ApiError;
  timestamp: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}
