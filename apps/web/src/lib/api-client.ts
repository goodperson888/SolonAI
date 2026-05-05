import axios from 'axios'

export type SolanaNetwork = 'mainnet' | 'devnet'

const resolveApiBaseUrl = () => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL
  }

  if (typeof window !== 'undefined') {
    return `${window.location.protocol}//${window.location.hostname}:8000`
  }

  return 'http://127.0.0.1:8000'
}

const API_BASE_URL = resolveApiBaseUrl()

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // AI 回复可能较慢，设置60秒超时
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // 统一错误处理
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// ===== AI 对话 API =====

export interface ChatRequest {
  message: string
  wallet_address?: string
  session_id?: string
}

export interface ChatResponse {
  reply: string
  intent: string
  intent_params: Record<string, unknown>
  session_id: string
  data?: ChatMessageData
}

export interface ChatStrategyStep {
  step?: number
  action?: string
  protocol?: string
  token?: string
  amount?: number
  expected_apy?: number
  description?: string
}

export interface ChatStrategyDraft {
  title?: string
  strategy_name?: string
  protocol?: string
  protocol_name?: string
  estimated_apy?: number
  expected_apy?: number
  risk_level?: string
  protocols?: string[]
  steps?: ChatStrategyStep[]
}

export interface ChatRiskAssessment {
  risk_level?: string
  is_safe?: boolean
  score?: number
  warnings?: string[]
  blockers?: string[]
  checks?: Array<{
    item: string
    status: string
    detail: string
  }>
}

export interface ChatApprovalPreview {
  intent?: string
  wallet_address?: string
  strategy_name?: string
  risk_level?: string
  expected_apy?: number
  protocols?: string[]
  steps?: ChatStrategyStep[]
  risk_score?: number
  risk_warnings?: string[]
  risk_blockers?: string[]
  validation_passed?: boolean
  validation_warnings?: string[]
  message?: string
}

export interface ChatWalletAssetSummary {
  symbol?: string
  balance?: number
  usd_value?: number
}

export interface ChatTransactionSummary {
  id?: string
  tx_type?: string
  status?: string
  network?: SolanaNetwork
  execution_mode?: 'auto' | 'simulate' | 'build'
  tx_payload?: Record<string, unknown>
  simulation_result?: Record<string, unknown>
}

export interface ChatMessageData {
  strategy?: ChatStrategyDraft
  risk_assessment?: ChatRiskAssessment
  wallet_assets?: ChatWalletAssetSummary[]
  transaction?: ChatTransactionSummary
  total_value_usd?: number | null
  stream_progress?: {
    strategy?: boolean
    risk_assessment?: boolean
    wallet_assets?: boolean
    approval_preview?: boolean
  }
  validation?: {
    is_valid?: boolean
    warnings?: string[]
  }
  approval_preview?: ChatApprovalPreview
  interrupted?: boolean
  thread_id?: string
  saved_strategy_id?: string
  monitoring?: Record<string, unknown>
}

export interface ChatCardPatchEvent {
  card: 'strategy' | 'risk_assessment' | 'wallet_assets' | 'approval_preview' | string
  intent: string
  intent_params: Record<string, unknown>
  data?: ChatMessageData
}

export interface ChatSessionItem {
  id: string
  session_id: string
  title?: string
  created_at: string
}

export interface ChatMessageItem {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  intent?: string
  created_at: string
  extra_data?: ChatMessageData
}

export const chatApi = {
  /**
   * 发送消息给 AI
   */
  sendMessage: (request: ChatRequest): Promise<ChatResponse> => {
    return apiClient.post('/api/v1/chat/message', request)
  },

  /**
   * 流式发送消息给 AI（SSE）
   * 逐字返回 AI 回复，体验更好
   */
  sendMessageStream: (
    request: ChatRequest,
    callbacks: {
      onToken: (token: string) => void
      onData?: (data: {
        intent: string
        intent_params: Record<string, unknown>
        data?: ChatMessageData
      }) => void
      onCardPatch?: (patch: ChatCardPatchEvent) => void
      onSession?: (sessionId: string) => void
      onRagSources?: (sources: { filename: string }[]) => void
      onAgentStatus?: (status: {
        agent: string
        status: 'running' | 'done'
        message: string
      }) => void
      onDone: () => void
      onError: (error: string) => void
    }
  ): { abort: () => void } => {
    const controller = new AbortController()

    fetch(`${API_BASE_URL}/api/v1/chat/message/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          const err = await response.json().catch(() => ({ detail: '请求失败' }))
          callbacks.onError(err.detail || '请求失败')
          return
        }

        const reader = response.body?.getReader()
        if (!reader) {
          callbacks.onError('无法读取响应流')
          return
        }

        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          let eventType = ''
          for (const line of lines) {
            if (line.startsWith('event: ')) {
              eventType = line.slice(7).trim()
            } else if (line.startsWith('data: ')) {
              const data = line.slice(6)
              try {
                const parsed = JSON.parse(data)
                if (eventType === 'token') {
                  callbacks.onToken(parsed.token)
                } else if (eventType === 'data') {
                  callbacks.onData?.(parsed)
                } else if (eventType === 'card_patch') {
                  callbacks.onCardPatch?.(parsed)
                } else if (eventType === 'session') {
                  callbacks.onSession?.(parsed.session_id)
                } else if (eventType === 'rag_sources') {
                  callbacks.onRagSources?.(parsed.sources)
                } else if (eventType === 'agent_status') {
                  callbacks.onAgentStatus?.(parsed)
                } else if (eventType === 'done') {
                  callbacks.onDone()
                } else if (eventType === 'error') {
                  callbacks.onError(parsed.error)
                }
              } catch {
                // ignore parse errors
              }
            }
          }
        }
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          callbacks.onError(err.message || 'AI 服务不可用')
        }
      })

    return { abort: () => controller.abort() }
  },

  /**
   * AI 服务健康检查
   */
  healthCheck: (): Promise<{ status: string }> => {
    return apiClient.get('/api/v1/chat/health')
  },

  /**
   * 获取会话列表
   */
  getSessions: (walletAddress: string, limit = 20): Promise<ChatSessionItem[]> => {
    return apiClient.get('/api/v1/chat/sessions', {
      params: { wallet_address: walletAddress, limit },
    })
  },

  /**
   * 获取会话消息
   */
  getMessages: (sessionId: string, limit = 100): Promise<ChatMessageItem[]> => {
    return apiClient.get(`/api/v1/chat/sessions/${sessionId}/messages`, {
      params: { limit },
    })
  },

  /**
   * 删除会话
   */
  deleteSession: (
    sessionId: string,
    walletAddress: string
  ): Promise<{ success: boolean; message: string }> => {
    return apiClient.delete(`/api/v1/chat/sessions/${sessionId}`, {
      params: { wallet_address: walletAddress },
    })
  },

  approveAction: (threadId: string, userApproved: boolean): Promise<ApprovalResponse> => {
    return apiClient.post(`/api/v1/chat/threads/${threadId}/approval`, {
      user_approved: userApproved,
    })
  },

  getThreadState: (threadId: string): Promise<ThreadStateResponse> => {
    return apiClient.get(`/api/v1/chat/threads/${threadId}/state`)
  },
}

// ===== 资产 API =====

export interface TokenAsset {
  mint: string
  symbol: string
  name: string
  balance: number
  decimals: number
  usd_value: number
  price_usd: number
}

export interface WalletAssetsResponse {
  wallet_address: string
  sol_balance: number
  sol_price_usd: number
  sol_value_usd: number
  tokens: TokenAsset[]
  total_value_usd: number
  queried_network?: string
  alternate_network?: string | null
  alternate_sol_balance?: number | null
  network_hint?: string | null
}

export interface AssetDiagnosisResponse {
  wallet_address: string
  risk_level: 'low' | 'medium' | 'high'
  risk_score: number
  issues: Array<{
    type: string
    severity: string
    description: string
    recommendation: string
  }>
  health_metrics: {
    diversification_score: number
    liquidity_score: number
    volatility_score: number
  }
}

export interface PnLResponse {
  wallet_address: string
  total_pnl: number
  total_pnl_percentage: number
  realized_pnl: number
  unrealized_pnl: number
  roi_percentage: number
  breakdown?: Array<{
    asset: string
    type: string
    pnl: number
    percentage: number
  }>
}

export const assetsApi = {
  /**
   * 获取钱包资产
   */
  getWalletAssets: (
    walletAddress: string,
    network: SolanaNetwork
  ): Promise<WalletAssetsResponse> => {
    return apiClient.get(`/api/v1/assets/${walletAddress}`, { params: { network } })
  },

  /**
   * 获取资产诊断
   */
  getDiagnosis: (
    walletAddress: string,
    network: SolanaNetwork
  ): Promise<AssetDiagnosisResponse> => {
    return apiClient.get(`/api/v1/assets/${walletAddress}/diagnosis`, { params: { network } })
  },

  /**
   * 获取盈亏分析
   */
  getPnL: (walletAddress: string, network: SolanaNetwork): Promise<PnLResponse> => {
    return apiClient.get(`/api/v1/assets/${walletAddress}/pnl`, { params: { network } })
  },
}

// ===== 策略 API =====

export interface StrategyGenerateRequest {
  wallet_address: string
  amount: number
  token: string
  risk_level: 'conservative' | 'balanced' | 'aggressive'
  duration: number
  network?: SolanaNetwork
}

export interface Strategy {
  id: string
  title: string
  summary?: string
  strategy_type: string
  risk_level: string
  estimated_apy?: number
  protocol_name?: string
  input_token: string
  input_amount?: number
  steps: Array<{
    step: number
    action: string
    protocol: string
    token: string
    amount: number
    expected_apy: number
    description: string
  }>
  risk_assessment: {
    risk_level: string
    is_safe: boolean
    score: number
    checks: Array<{
      item: string
      status: string
      detail: string
    }>
    warnings: string[]
    blockers: string[]
  }
  status: string
  created_at: string
}

export interface TransactionResponse {
  id: string
  tx_type: string
  status: string
  from_token?: string
  to_token?: string
  amount?: number
  tx_payload: Record<string, unknown>
  simulation_result: Record<string, unknown>
  network: SolanaNetwork
  execution_mode: 'auto' | 'simulate' | 'build'
  created_at: string
}

export interface StrategyCapabilitiesResponse {
  demo_mode: boolean
  summary: {
    real_execution_supported: string[]
    preview_only: string[]
    market_data_only: string[]
  }
  protocols: Record<
    string,
    {
      market_data: boolean
      strategy_generation: boolean
      devnet_execution: boolean
      mainnet_execution: boolean
      wallet_signature: boolean
      notes: string
    }
  >
  testing_guidance: {
    works_well_on_devnet_or_demo: string[]
    requires_mainnet_for_real_validation: string[]
    best_demo_approach: string
  }
}

export interface ApprovalResponse {
  reply: string
  intent: string
  intent_params: Record<string, unknown>
  data?: ChatMessageData
  thread_id: string
  interrupted: boolean
}

export interface ThreadStateResponse {
  thread_id: string
  interrupted: boolean
  next: string[]
}

export const strategyApi = {
  /**
   * 生成投资策略
   */
  generateStrategy: (request: StrategyGenerateRequest): Promise<Strategy> => {
    return apiClient.post('/api/v1/strategy/generate', request)
  },

  saveStrategyDraft: (request: {
    wallet_address: string
    strategy: ChatStrategyDraft
    risk_assessment?: ChatRiskAssessment
    summary?: string
  }): Promise<Strategy> => {
    return apiClient.post('/api/v1/strategy/save-draft', request)
  },

  /**
   * 获取策略列表
   */
  listStrategies: (walletAddress: string): Promise<{ strategies: Strategy[] }> => {
    return apiClient.get('/api/v1/strategy/list', { params: { wallet_address: walletAddress } })
  },

  /**
   * 获取策略详情
   */
  getStrategy: (strategyId: string): Promise<Strategy> => {
    return apiClient.get(`/api/v1/strategy/${strategyId}`)
  },

  /**
   * 执行策略
   */
  executeStrategy: (
    strategyId: string,
    walletAddress: string,
    network: SolanaNetwork,
    executionMode: 'auto' | 'simulate' | 'build' = 'auto'
  ): Promise<TransactionResponse> => {
    return apiClient.post(`/api/v1/strategy/${strategyId}/execute`, {
      wallet_address: walletAddress,
      network,
      execution_mode: executionMode,
    })
  },

  completePreparedTransaction: (
    transactionId: string,
    signature: string,
    status: 'submitted' | 'confirmed'
  ): Promise<TransactionResponse> => {
    return apiClient.post(`/api/v1/strategy/transactions/${transactionId}/complete`, {
      signature,
      status,
    })
  },

  getCapabilities: (): Promise<StrategyCapabilitiesResponse> => {
    return apiClient.get('/api/v1/strategy/meta/capabilities')
  },
}

// ===== 风控 API =====

export interface RiskAssessment {
  wallet_address: string
  overall_risk_score: number
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  risk_factors: Array<{
    factor: string
    score: number
    description: string
    impact: string
  }>
  recommendations: string[]
  last_updated: string
}

export interface Transaction {
  signature: string
  timestamp: string
  type: string
  status: 'success' | 'failed' | 'pending'
  amount?: number
  token?: string
  from?: string
  to?: string
  risk_score?: number
  risk_flags?: string[]
}

export interface RiskAlert {
  id: string
  wallet_address: string
  alert_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  title: string
  description: string
  created_at: string
  resolved: boolean
}

export interface Authorization {
  id: string
  wallet_address: string
  program_id: string
  program_name: string
  permissions: string[]
  granted_at: string
  last_used?: string
  risk_level: string
}

export const riskApi = {
  /**
   * 获取风险评估
   */
  assessment: (walletAddress: string, network: SolanaNetwork): Promise<RiskAssessment> => {
    return apiClient.get('/api/v1/risk/assessment', {
      params: { wallet_address: walletAddress, network },
    })
  },

  /**
   * 获取交易历史
   */
  transactions: (
    walletAddress: string,
    limit?: number
  ): Promise<{ transactions: Transaction[] }> => {
    return apiClient.get('/api/v1/risk/transactions', {
      params: { wallet_address: walletAddress, limit },
    })
  },

  /**
   * 获取风险预警
   */
  alerts: (walletAddress: string): Promise<{ alerts: RiskAlert[] }> => {
    return apiClient.get('/api/v1/risk/alerts', { params: { wallet_address: walletAddress } })
  },

  /**
   * 获取授权管理
   */
  authorizations: (
    walletAddress: string,
    network: SolanaNetwork
  ): Promise<{ authorizations: Authorization[] }> => {
    return apiClient.get('/api/v1/risk/authorizations', {
      params: { wallet_address: walletAddress, network },
    })
  },

  /**
   * 撤销授权
   */
  revokeAuth: (
    authId: string,
    walletAddress: string
  ): Promise<{ success: boolean; message: string }> => {
    return apiClient.post(`/api/v1/risk/authorizations/${authId}/revoke`, {
      wallet_address: walletAddress,
    })
  },
}

// ===== 知识库 API =====

export interface KnowledgeDocument {
  id: string
  user_id: string
  filename: string
  file_type: string
  file_size: number
  chunk_count: number
  upload_time: string
  metadata?: Record<string, unknown>
}

export interface KnowledgeStats {
  total_documents: number
  total_chunks: number
  total_size_bytes: number
  document_types: Record<string, number>
}

export interface KnowledgeSearchResult {
  chunk_id: string
  document_id: string
  filename: string
  content: string
  score: number
  metadata?: Record<string, unknown>
}

export const knowledgeApi = {
  /**
   * 上传知识文档
   */
  upload: (
    file: File,
    walletAddress: string,
    metadata?: Record<string, unknown>
  ): Promise<{ document: KnowledgeDocument }> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('wallet_address', walletAddress)
    if (metadata) {
      formData.append('metadata', JSON.stringify(metadata))
    }
    return apiClient.post('/api/v1/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  /**
   * 获取文档列表
   */
  listDocuments: (walletAddress: string): Promise<{ documents: KnowledgeDocument[] }> => {
    return apiClient.get('/api/v1/knowledge/documents', {
      params: { wallet_address: walletAddress },
    })
  },

  /**
   * 删除文档
   */
  deleteDocument: (
    documentId: string,
    walletAddress: string
  ): Promise<{ success: boolean; message: string }> => {
    return apiClient.delete(`/api/v1/knowledge/documents/${documentId}`, {
      params: { wallet_address: walletAddress },
    })
  },

  /**
   * 搜索知识库
   */
  search: (
    query: string,
    walletAddress: string,
    topK?: number
  ): Promise<{ results: KnowledgeSearchResult[] }> => {
    return apiClient.post('/api/v1/knowledge/search', {
      query,
      wallet_address: walletAddress,
      top_k: topK,
    })
  },

  /**
   * 获取知识库统计
   */
  stats: (walletAddress: string): Promise<KnowledgeStats> => {
    return apiClient.get('/api/v1/knowledge/stats', { params: { wallet_address: walletAddress } })
  },
}
