import type { Metadata } from 'next'
import dynamic from 'next/dynamic'
import './globals.css'
import '@solana/wallet-adapter-react-ui/styles.css'

// 禁用 SSR，避免 wallet provider 在服务端渲染时报错
const Providers = dynamic(() => import('@/components/providers/Providers'), {
  ssr: false,
})

export const metadata: Metadata = {
  title: 'Solon AI - Solana生态AI金融智能体',
  description: 'Solana生态全链路非托管AI金融智能体，你的链上资产专属管家',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-slate-950 text-white antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
