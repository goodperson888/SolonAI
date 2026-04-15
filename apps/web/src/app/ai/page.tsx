'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { MessageBubble } from '@/components/chat/MessageBubble'
import { mockMessages } from '@/data/mockMessages'

interface Conversation {
  id: string
  title: string
  lastMessage: string
  timestamp: string
  messageCount: number
}

export default function AIAssistantPage() {
  const [conversations] = useState<Conversation[]>([
    {
      id: '1',
      title: '如何优化我的资产配置？',
      lastMessage: '建议将 30% 的资产配置到稳定币...',
      timestamp: '2分钟前',
      messageCount: 8,
    },
    {
      id: '2',
      title: 'MarginFi 借贷安全吗？',
      lastMessage: 'MarginFi 已通过多次审计，是 Solana...',
      timestamp: '1小时前',
      messageCount: 5,
    },
    {
      id: '3',
      title: '帮我分析一下 SOL 的走势',
      lastMessage: '根据链上数据分析，SOL 近期...',
      timestamp: '昨天',
      messageCount: 12,
    },
    {
      id: '4',
      title: '如何参与流动性挖矿？',
      lastMessage: '流动性挖矿的基本步骤是...',
      timestamp: '2天前',
      messageCount: 6,
    },
  ])

  const [activeConversation, setActiveConversation] = useState('1')
  const [inputMessage, setInputMessage] = useState('')

  const handleSend = () => {
    if (!inputMessage.trim()) return
    // TODO: 发送消息逻辑
    setInputMessage('')
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* 左侧：对话列表 */}
      <div className="flex w-80 flex-col border-r border-gray-800 bg-gray-900">
        {/* 头部 */}
        <div className="flex-shrink-0 border-b border-gray-800 p-4">
          <Button variant="primary" size="md" className="w-full">
            + 新建对话
          </Button>
        </div>

        {/* 对话列表 */}
        <div className="flex-1 overflow-y-auto">
          <div className="space-y-1 p-2">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => setActiveConversation(conv.id)}
                className={`w-full rounded-lg p-3 text-left transition-colors ${
                  activeConversation === conv.id
                    ? 'border border-indigo-500/50 bg-indigo-600/20'
                    : 'hover:bg-gray-800'
                }`}
              >
                <div className="mb-1 flex items-start justify-between">
                  <h3 className="line-clamp-1 text-sm font-medium text-white">{conv.title}</h3>
                  <span className="ml-2 flex-shrink-0 text-xs text-gray-500">{conv.timestamp}</span>
                </div>
                <p className="mb-1 line-clamp-2 text-xs text-gray-400">{conv.lastMessage}</p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">{conv.messageCount} 条消息</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* 底部信息 */}
        <div className="flex-shrink-0 border-t border-gray-800 p-4">
          <div className="text-center text-xs text-gray-500">
            <p>Powered by Solon AI</p>
            <p className="mt-1">基于 LangGraph 多智能体</p>
          </div>
        </div>
      </div>

      {/* 右侧：对话内容 */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* 对话头部 */}
        <div className="flex h-16 flex-shrink-0 items-center justify-between border-b border-gray-800 bg-gray-900/50 px-6">
          <div>
            <h2 className="text-lg font-semibold text-white">
              {conversations.find((c) => c.id === activeConversation)?.title}
            </h2>
            <p className="text-xs text-gray-400">AI 智能助手 · 实时响应</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm">
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
                />
              </svg>
            </Button>
          </div>
        </div>

        {/* 消息区域 */}
        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-6">
          {mockMessages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {/* 快捷操作建议 */}
          <div className="mt-6 flex flex-wrap gap-2">
            <button className="rounded-lg bg-gray-800 px-4 py-2 text-sm text-gray-300 transition-colors hover:bg-gray-700">
              💰 分析我的资产配置
            </button>
            <button className="rounded-lg bg-gray-800 px-4 py-2 text-sm text-gray-300 transition-colors hover:bg-gray-700">
              📊 推荐收益策略
            </button>
            <button className="rounded-lg bg-gray-800 px-4 py-2 text-sm text-gray-300 transition-colors hover:bg-gray-700">
              🛡️ 检查安全风险
            </button>
            <button className="rounded-lg bg-gray-800 px-4 py-2 text-sm text-gray-300 transition-colors hover:bg-gray-700">
              ⚡ 查看套利机会
            </button>
          </div>
        </div>

        {/* 输入区域 */}
        <div className="flex-shrink-0 border-t border-gray-800 bg-gray-900/50 p-4">
          <div className="mx-auto max-w-4xl">
            <div className="flex items-end gap-3">
              <div className="relative flex-1">
                <textarea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault()
                      handleSend()
                    }
                  }}
                  placeholder="输入您的问题，Shift + Enter 换行..."
                  className="w-full resize-none rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-white focus:border-indigo-500 focus:outline-none"
                  rows={3}
                />
                <div className="absolute bottom-3 right-3 flex items-center gap-2">
                  <button className="p-1.5 text-gray-400 transition-colors hover:text-white">
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
                      />
                    </svg>
                  </button>
                </div>
              </div>
              <Button
                variant="primary"
                size="lg"
                onClick={handleSend}
                disabled={!inputMessage.trim()}
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              </Button>
            </div>
            <div className="mt-2 text-center text-xs text-gray-500">
              AI 可能会出错，请核实重要信息
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
