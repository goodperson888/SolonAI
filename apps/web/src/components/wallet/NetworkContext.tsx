'use client'

import {
  createContext,
  ReactNode,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'

export type SolanaNetwork = 'mainnet' | 'devnet'

type NetworkContextValue = {
  network: SolanaNetwork
  setNetwork: (network: SolanaNetwork) => void
  toggleNetwork: () => void
}

const STORAGE_KEY = 'solon:selected-network'

const NetworkContext = createContext<NetworkContextValue | null>(null)

export function NetworkProvider({ children }: { children: ReactNode }) {
  const [network, setNetworkState] = useState<SolanaNetwork>('mainnet')

  useEffect(() => {
    const saved = window.localStorage.getItem(STORAGE_KEY)
    if (saved === 'mainnet' || saved === 'devnet') {
      setNetworkState(saved)
    }
  }, [])

  const setNetwork = (nextNetwork: SolanaNetwork) => {
    setNetworkState(nextNetwork)
    window.localStorage.setItem(STORAGE_KEY, nextNetwork)
  }

  const value = useMemo(
    () => ({
      network,
      setNetwork,
      toggleNetwork: () => setNetwork(network === 'mainnet' ? 'devnet' : 'mainnet'),
    }),
    [network]
  )

  return <NetworkContext.Provider value={value}>{children}</NetworkContext.Provider>
}

export function useSolanaNetwork() {
  const context = useContext(NetworkContext)
  if (!context) {
    throw new Error('useSolanaNetwork must be used within NetworkProvider')
  }
  return context
}
