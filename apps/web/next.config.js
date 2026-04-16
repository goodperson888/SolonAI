/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@solon-ai/ui', '@solon-ai/types', '@solon-ai/utils'],
  // 跳过错误页面的静态生成
  experimental: {
    missingSuspenseWithCSRBailout: false,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_SOLANA_RPC_URL:
      process.env.NEXT_PUBLIC_SOLANA_RPC_URL || 'https://api.devnet.solana.com',
    NEXT_PUBLIC_WALLET_ADAPTER_NETWORK: process.env.NEXT_PUBLIC_WALLET_ADAPTER_NETWORK || 'devnet',
  },
  // 允许构建时出现错误页面预渲染失败
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: false,
  },
}

module.exports = nextConfig
