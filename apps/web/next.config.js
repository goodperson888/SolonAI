/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@solon-ai/ui', '@solon-ai/types', '@solon-ai/utils'],
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_SOLANA_RPC_URL:
      process.env.NEXT_PUBLIC_SOLANA_RPC_URL || 'https://api.devnet.solana.com',
    NEXT_PUBLIC_WALLET_ADAPTER_NETWORK: process.env.NEXT_PUBLIC_WALLET_ADAPTER_NETWORK || 'devnet',
  },
  // 配置 webpack 以避免 styled-jsx 在 SSR 时的问题
  webpack: (config, { isServer }) => {
    if (isServer) {
      // 服务端渲染时排除某些模块
      config.externals = config.externals || []
      config.externals.push({
        'styled-jsx': 'styled-jsx',
      })
    }
    return config
  },
}

module.exports = nextConfig
