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
}

module.exports = nextConfig
