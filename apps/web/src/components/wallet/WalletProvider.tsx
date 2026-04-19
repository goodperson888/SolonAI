'use client'

import { FC, ReactNode, useMemo } from 'react'
import dynamic from 'next/dynamic'
import {
  ConnectionProvider,
  WalletProvider as SolanaWalletProvider,
} from '@solana/wallet-adapter-react'
import { WalletAdapterNetwork } from '@solana/wallet-adapter-base'
import { PhantomWalletAdapter } from '@solana/wallet-adapter-phantom'
import { WalletModalProvider } from '@solana/wallet-adapter-react-ui'
import { SolflareWalletAdapter } from '@solana/wallet-adapter-solflare'
import { clusterApiUrl } from '@solana/web3.js'

interface WalletProviderProps {
  children: ReactNode
}

const WalletProviderInner: FC<WalletProviderProps> = ({ children }) => {
  const network =
    (process.env.NEXT_PUBLIC_WALLET_ADAPTER_NETWORK as WalletAdapterNetwork) ||
    WalletAdapterNetwork.Devnet
  const endpoint = useMemo(() => {
    if (process.env.NEXT_PUBLIC_SOLANA_RPC_URL) {
      return process.env.NEXT_PUBLIC_SOLANA_RPC_URL
    }
    return clusterApiUrl(network)
  }, [network])

  const wallets = useMemo(() => [new PhantomWalletAdapter(), new SolflareWalletAdapter()], [])

  return (
    <ConnectionProvider endpoint={endpoint}>
      <SolanaWalletProvider wallets={wallets} autoConnect>
        <WalletModalProvider>{children}</WalletModalProvider>
      </SolanaWalletProvider>
    </ConnectionProvider>
  )
}

export const WalletProvider = dynamic(() => Promise.resolve(WalletProviderInner), {
  ssr: false,
})
