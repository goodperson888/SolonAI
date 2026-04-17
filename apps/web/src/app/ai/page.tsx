'use client'

import { useState, useRef, useEffect } from 'react'
import { useWallet } from '@solana/wallet-adapter-react'
import { Button } from '@/components/ui/Button'
import { MessageBubble } from '@/components/chat/MessageBubble'
import { chatApi } from '@/lib/api-client'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  intent?: string
  data?: Record<string, unknown>
}

interface Conversation {
  id: string
  title: string
  messages: Message[]
  sessionId: string
  timestamp: string
}

export default function AIAssistantPage() {
  const { connected, publicKey } = useWallet()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const activeConversation = conversations.find((c) => c.id === activeConversationId)
  const messages = activeConversation?.messages || []

  // 自动滚动到底部（仅在有消息时）
  useEffect(() => {
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  // 创建新对话
  const createNewConversation = () => {
    const newConv: Conversation = {
      id: Date.now().toString(),
      title: '新对话',
      messages: [],
      sessionId: '',
      timestamp: '刚刚',
    }
    setConversations((prev) => [newConv, ...prev])
    setActiveConversationId(newConv.id)
  }

  // 如果没有对话，自动创建一个
  useEffect(() => {
    if (conversations.length === 0) {
      createNewConversation()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSend = async () => {
    if (!inputMessage.trim() || isLoading || !activeConversationId) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    }

    // 添加用户消息到当前对话
    setConversations((prev) =>
      prev.map((conv) => {
        if (conv.id !== activeConversationId) return conv
        const updated = {
          ...conv,
          messages: [...conv.messages, userMessage],
          // 用第一条消息作为对话标题
          title: conv.messages.length === 0 ? inputMessage.slice(0, 20) : conv.title,
          timestamp: '刚刚',
        }
        return updated
      })
    )

    const currentInput = inputMessage
    setInputMessage('')
    setIsLoading(true)

    try {
      const response = await chatApi.sendMessage({
        message: currentInput,
        wallet_address: connected && publicKey ? publicKey.toBase58() : '',
        session_id: activeConversation?.sessionId || '',
      })

      // 保存 session_id
      if (response.session_id) {
        setConversations((prev) =>
          prev.map((conv) =>
            conv.id === activeConversationId ? { ...conv, sessionId: response.session_id } : conv
          )
        )
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.reply,
        timestamp: new Date(),
        intent: response.intent,
        data: response.data || undefined,
      }

      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === activeConversationId
            ? { ...conv, messages: [...conv.messages, aiMessage] }
            : conv
        )
      )
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '抱歉，AI 服务暂时不可用。请确保后端服务已启动。',
        timestamp: new Date(),
      }
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === activeConversationId
            ? { ...conv, messages: [...conv.messages, errorMessage] }
            : conv
        )
      )
      console.error('Chat API error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuickAction = (text: string) => {
    setInputMessage(text)
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* 左侧：对话列表 */}
      <div className="flex w-80 flex-col border-r border-gray-800 bg-gray-900">
        {/* 头部 */}
        <div className="flex-shrink-0 border-b border-gray-800 p-4">
          <Button variant="primary" size="md" className="w-full" onClick={createNewConversation}>
            + 新建对话
          </Button>
        </div>

        {/* 对话列表 */}
        <div className="flex-1 overflow-y-auto">
          <div className="space-y-1 p-2">
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => setActiveConversationId(conv.id)}
                className={`w-full rounded-lg p-3 text-left transition-colors ${
                  activeConversationId === conv.id
                    ? 'border border-indigo-500/50 bg-indigo-600/20'
                    : 'hover:bg-gray-800'
                }`}
              >
                <div className="mb-1 flex items-start justify-between">
                  <h3 className="line-clamp-1 text-sm font-medium text-white">{conv.title}</h3>
                  <span className="ml-2 flex-shrink-0 text-xs text-gray-500">{conv.timestamp}</span>
                </div>
                <p className="mb-1 line-clamp-2 text-xs text-gray-400">
                  {conv.messages.length > 0
                    ? conv.messages[conv.messages.length - 1].content.slice(0, 50)
                    : '开始新的对话...'}
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">{conv.messages.length} 条消息</span>
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
              {activeConversation?.title || '新对话'}
            </h2>
            <p className="text-xs text-gray-400">AI 智能助手 · 实时响应</p>
          </div>
        </div>

        {/* 消息区域 */}
        <div className="min-h-0 flex-1 space-y-4 overflow-y-auto p-6">
          {messages.length === 0 ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <div className="mb-4 text-4xl">💬</div>
                <p className="text-gray-400">开始与 AI 助手对话</p>
                <p className="mt-2 text-sm text-gray-500">
                  你可以询问关于 DeFi、资产管理、策略推荐等问题
                </p>
                {/* 快捷操作建议 */}
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {[
                    '💰 分析我的资产配置',
                    '📊 推荐收益策略',
                    '🛡️ 检查安全风险',
                    '⚡ 查看套利机会',
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => handleQuickAction(suggestion)}
                      className="rounded-lg bg-gray-800 px-4 py-2 text-sm text-gray-300 transition-colors hover:bg-gray-700"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            messages.map((message) => <MessageBubble key={message.id} message={message} />)
          )}

          {isLoading && (
            <div className="flex items-center space-x-2 text-gray-400">
              <div className="h-2 w-2 animate-bounce rounded-full bg-indigo-400" />
              <div
                className="h-2 w-2 animate-bounce rounded-full bg-indigo-400"
                style={{ animationDelay: '0.1s' }}
              />
              <div
                className="h-2 w-2 animate-bounce rounded-full bg-indigo-400"
                style={{ animationDelay: '0.2s' }}
              />
              <span className="ml-2 text-sm">AI 正在思考...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
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
                  disabled={isLoading}
                />
              </div>
              <Button
                variant="primary"
                size="lg"
                onClick={handleSend}
                disabled={!inputMessage.trim() || isLoading}
              >
                {isLoading ? (
                  '...'
                ) : (
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                    />
                  </svg>
                )}
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
