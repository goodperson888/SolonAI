/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@solon-ai/ui', '@solon-ai/types', '@solon-ai/utils'],
  experimental: {
    // 跳过错误页面的静态生成，避免 SSR 时 wallet provider 报错
    skipTrailingSlashRedirect: true,
  },
  // 禁用静态导出错误页面
  generateBuildId: async () => {
    return 'build-id'
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_SOLANA_RPC_URL:
      process.env.NEXT_PUBLIC_SOLANA_RPC_URL || 'https://api.devnet.solana.com',
    NEXT_PUBLIC_WALLET_ADAPTER_NETWORK: process.env.NEXT_PUBLIC_WALLET_ADAPTER_NETWORK || 'devnet',
  },
}

module.exports = nextConfig
