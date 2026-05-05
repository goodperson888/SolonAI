'use client'

import { useState, useRef, useEffect } from 'react'
import { useWallet } from '@solana/wallet-adapter-react'
import { Button } from '@/components/ui/Button'
import { MessageBubble } from './MessageBubble'
import { useTranslation } from '@/hooks/useTranslation'
import { chatApi, strategyApi, type ChatMessageData, type ChatMessageItem } from '@/lib/api-client'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  intent?: string
  data?: ChatMessageData
}

const STORAGE_KEY_PREFIX = 'solon-ai:chat:'
const GLOBAL_STORAGE_KEY = `${STORAGE_KEY_PREFIX}last`

function getStorageKey(walletAddress?: string): string {
  return `${STORAGE_KEY_PREFIX}${walletAddress || 'guest'}`
}

function fromApiMessage(message: ChatMessageItem): Message {
  return {
    id: message.id,
    role: message.role === 'system' ? 'assistant' : message.role,
    content: message.content,
    timestamp: new Date(message.created_at),
    intent: message.intent,
    data: message.extra_data,
  }
}

export const ChatWindow: React.FC = () => {
  const { t } = useTranslation()
  const { connected, publicKey } = useWallet()
  const walletAddress = connected && publicKey ? publicKey.toBase58() : ''
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const [sessionId, setSessionId] = useState('')
  const [approvingThreadId, setApprovingThreadId] = useState<string | null>(null)
  const [savingStrategyMessageId, setSavingStrategyMessageId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    const loadHistory = async () => {
      setIsLoadingHistory(true)

      try {
        if (walletAddress) {
          const sessions = await chatApi.getSessions(walletAddress, 1)
          const latestSession = sessions[0]
          if (latestSession) {
            const history = await chatApi.getMessages(latestSession.session_id)
            setSessionId(latestSession.session_id)
            setMessages(history.map(fromApiMessage))
            return
          }
        }

        for (const storageKey of [
          getStorageKey(walletAddress),
          GLOBAL_STORAGE_KEY,
          getStorageKey(),
        ]) {
          const saved = localStorage.getItem(storageKey)
          if (!saved) {
            continue
          }

          const parsed = JSON.parse(saved) as Array<{
            sessionId: string
            messages: Message[]
          }>
          const latestConversation = parsed[0]
          if (!latestConversation) {
            continue
          }

          setSessionId(latestConversation.sessionId || '')
          setMessages(
            (latestConversation.messages || []).map((message) => ({
              ...message,
              timestamp: new Date(message.timestamp),
            }))
          )
          return
        }

        setMessages([])
        setSessionId('')
      } catch (error) {
        console.error('Failed to restore chat window history:', error)
      } finally {
        setIsLoadingHistory(false)
      }
    }

    loadHistory()
  }, [walletAddress])

  useEffect(() => {
    if (isLoadingHistory) {
      return
    }

    if (messages.length === 0 && !sessionId) {
      return
    }

    const conversationSnapshot = [
      {
        id: sessionId || 'widget-session',
        title: messages[0]?.content?.slice(0, 20) || '新对话',
        sessionId,
        timestamp: '刚刚',
        messages,
      },
    ]

    const serialized = JSON.stringify(conversationSnapshot)
    localStorage.setItem(getStorageKey(walletAddress), serialized)
    localStorage.setItem(GLOBAL_STORAGE_KEY, serialized)
  }, [isLoadingHistory, messages, sessionId, walletAddress])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    const currentInput = input
    setInput('')
    setIsLoading(true)

    try {
      // 调用后端 AI 接口
      const response = await chatApi.sendMessage({
        message: currentInput,
        wallet_address: walletAddress,
        session_id: sessionId,
      })

      // 保存会话ID
      if (response.session_id) {
        setSessionId(response.session_id)
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.reply,
        timestamp: new Date(),
        intent: response.intent,
        data: response.data || undefined,
      }
      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      // API 调用失败，显示错误信息
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '抱歉，AI 服务暂时不可用。请确保后端服务已启动（python main.py）。',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
      console.error('Chat API error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuickAction = (prompt: string) => {
    setInput(prompt)
  }

  const handleApprovalAction = async (threadId: string, approved: boolean) => {
    setApprovingThreadId(threadId)
    try {
      const result = await chatApi.approveAction(threadId, approved)
      const aiMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: result.reply,
        timestamp: new Date(),
        intent: result.intent,
        data: result.data,
      }
      setMessages((prev) => [
        ...prev.map((message) =>
          message.data?.thread_id === threadId
            ? {
                ...message,
                data: {
                  ...message.data,
                  interrupted: false,
                  approval_preview: undefined,
                },
              }
            : message
        ),
        aiMessage,
      ])
    } catch (error) {
      console.error('Approval action failed:', error)
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: approved
            ? '这条 AI 执行请求已经失效或已处理，先重新生成一版策略再确认。'
            : '这条 AI 取消请求没有成功提交，可能当前线程已经结束。',
          timestamp: new Date(),
        },
      ])
    } finally {
      setApprovingThreadId(null)
    }
  }

  const handleSaveStrategy = async (messageId: string, data: ChatMessageData, content: string) => {
    if (!walletAddress || !data.strategy) return

    setSavingStrategyMessageId(messageId)
    try {
      const saved = await strategyApi.saveStrategyDraft({
        wallet_address: walletAddress,
        strategy: data.strategy,
        risk_assessment: data.risk_assessment,
        summary: content,
      })

      setMessages((prev) =>
        prev.map((message) =>
          message.id === messageId
            ? {
                ...message,
                data: {
                  ...message.data,
                  saved_strategy_id: saved.id,
                },
              }
            : message
        )
      )
    } catch (error) {
      console.error('Save strategy failed:', error)
    } finally {
      setSavingStrategyMessageId(null)
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* Messages */}
      <div className="flex-1 space-y-1 overflow-y-auto p-4">
        {isLoadingHistory ? (
          <div className="flex h-full items-center justify-center text-sm text-gray-400">
            正在恢复历史对话...
          </div>
        ) : messages.length === 0 ? (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <div className="mb-4 text-4xl">💬</div>
              <p className="text-gray-400">{t('chat.empty')}</p>
              <p className="mt-2 text-sm text-gray-500">{t('chat.emptyHint')}</p>
              {/* 快捷指令按钮 */}
              <div className="mt-6 flex flex-wrap justify-center gap-2">
                {[
                  '帮我看看钱包里有什么资产',
                  '推荐一个稳健的DeFi策略',
                  '什么是无常损失',
                  '帮我检查一下代币安全性',
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => {
                      setInput(suggestion)
                    }}
                    className="rounded-lg border border-gray-700 bg-gray-800/50 px-3 py-2 text-sm text-gray-300 transition-colors hover:border-indigo-500 hover:text-white"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <MessageBubble
              key={message.id}
              message={message}
              onQuickAction={handleQuickAction}
              onApprovalAction={handleApprovalAction}
              onSaveStrategy={walletAddress ? handleSaveStrategy : undefined}
              savingStrategyMessageId={savingStrategyMessageId}
              approvingThreadId={approvingThreadId}
            />
          ))
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

      {/* Input */}
      <div className="flex-shrink-0 border-t border-gray-700 p-4">
        <div className="flex space-x-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={t('chat.placeholder')}
            className="flex-1 rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-white placeholder-gray-500 focus:border-indigo-500 focus:outline-none"
          />
          <Button
            variant="primary"
            size="md"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
          >
            {isLoading ? '...' : t('chat.send')}
          </Button>
        </div>
      </div>
    </div>
  )
}
