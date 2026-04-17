import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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
  data?: Record<string, unknown>
}

export const chatApi = {
  /**
   * 发送消息给 AI
   */
  sendMessage: (request: ChatRequest): Promise<ChatResponse> => {
    return apiClient.post('/api/v1/chat/message', request)
  },

  /**
   * AI 服务健康检查
   */
  healthCheck: (): Promise<{ status: string }> => {
    return apiClient.get('/api/v1/chat/health')
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
}

export const assetsApi = {
  /**
   * 获取钱包资产
   */
  getWalletAssets: (walletAddress: string): Promise<WalletAssetsResponse> => {
    return apiClient.get(`/api/v1/assets/${walletAddress}`)
  },
}
