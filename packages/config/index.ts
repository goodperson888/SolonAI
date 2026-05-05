/**
 * 共享配置文件
 */

/**
 * Solana网络配置
 */
export const SOLANA_NETWORKS = {
  mainnet: {
    name: 'Mainnet Beta',
    rpcUrl: 'https://api.mainnet-beta.solana.com',
    wsUrl: 'wss://api.mainnet-beta.solana.com',
  },
  devnet: {
    name: 'Devnet',
    rpcUrl: 'https://api.devnet.solana.com',
    wsUrl: 'wss://api.devnet.solana.com',
  },
  testnet: {
    name: 'Testnet',
    rpcUrl: 'https://api.testnet.solana.com',
    wsUrl: 'wss://api.testnet.solana.com',
  },
} as const;

/**
 * 支持的钱包列表
 */
export const SUPPORTED_WALLETS = [
  {
    name: 'Phantom',
    url: 'https://phantom.app/',
    icon: '/wallets/phantom.svg',
  },
  {
    name: 'Solflare',
    url: 'https://solflare.com/',
    icon: '/wallets/solflare.svg',
  },
  {
    name: 'Backpack',
    url: 'https://backpack.app/',
    icon: '/wallets/backpack.svg',
  },
] as const;

/**
 * DeFi协议配置
 */
export const DEFI_PROTOCOLS = {
  jupiter: {
    name: 'Jupiter',
    type: 'swap',
    apiUrl: 'https://quote-api.jup.ag/v6',
    website: 'https://jup.ag',
  },
  marginfi: {
    name: 'MarginFi',
    type: 'lending',
    programId: 'MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA',
    website: 'https://marginfi.com',
  },
  kamino: {
    name: 'Kamino',
    type: 'lending',
    website: 'https://kamino.finance',
  },
  drift: {
    name: 'Drift',
    type: 'perpetual',
    website: 'https://drift.trade',
  },
} as const;

/**
 * 常用代币配置
 */
export const COMMON_TOKENS = {
  SOL: {
    symbol: 'SOL',
    name: 'Solana',
    mint: 'So11111111111111111111111111111111111111112',
    decimals: 9,
    logoURI: 'https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png',
  },
  USDC: {
    symbol: 'USDC',
    name: 'USD Coin',
    mint: 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
    decimals: 6,
    logoURI: 'https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v/logo.png',
  },
  USDT: {
    symbol: 'USDT',
    name: 'Tether USD',
    mint: 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
    decimals: 6,
    logoURI: 'https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB/logo.png',
  },
} as const;

/**
 * 风险等级配置
 */
export const RISK_LEVELS = {
  conservative: {
    label: '保守型',
    description: '低风险，稳健收益',
    maxLeverage: 1.5,
    maxSlippage: 0.005, // 0.5%
  },
  balanced: {
    label: '稳健型',
    description: '中等风险，平衡收益',
    maxLeverage: 2.5,
    maxSlippage: 0.01, // 1%
  },
  aggressive: {
    label: '进取型',
    description: '高风险，高收益',
    maxLeverage: 5,
    maxSlippage: 0.03, // 3%
  },
} as const;

/**
 * API配置
 */
export const API_CONFIG = {
  timeout: 30000, // 30秒
  retryAttempts: 3,
  retryDelay: 1000, // 1秒
} as const;

/**
 * 分页配置
 */
export const PAGINATION = {
  defaultPageSize: 20,
  maxPageSize: 100,
} as const;

/**
 * 缓存配置
 */
export const CACHE_CONFIG = {
  tokenList: 3600, // 1小时
  userAssets: 60, // 1分钟
  prices: 30, // 30秒
} as const;
