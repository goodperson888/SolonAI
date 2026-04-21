'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { useWallet } from '@solana/wallet-adapter-react'
import { Button } from '@/components/ui/Button'
import { MessageBubble } from '@/components/chat/MessageBubble'
import { chatApi, knowledgeApi, type KnowledgeDocument } from '@/lib/api-client'
import { Upload, X, FileText, Trash2, MessageSquare, BookOpen } from 'lucide-react'

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

const INITIAL_CONVERSATION_ID = crypto.randomUUID()

export default function AIAssistantPage() {
  const { connected, publicKey } = useWallet()
  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: INITIAL_CONVERSATION_ID,
      title: '新对话',
      messages: [],
      sessionId: '',
      timestamp: '刚刚',
    },
  ])
  const [activeConversationId, setActiveConversationId] = useState<string>(INITIAL_CONVERSATION_ID)
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [leftPanelMode, setLeftPanelMode] = useState<'conversations' | 'knowledge'>('conversations')
  const [knowledgeDocs, setKnowledgeDocs] = useState<KnowledgeDocument[]>([])
  const [uploading, setUploading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  // 用 ref 追踪 activeConversationId，避免闭包问题
  const activeIdRef = useRef(activeConversationId)
  activeIdRef.current = activeConversationId

  const activeConversation = conversations.find((c) => c.id === activeConversationId)
  const messages = activeConversation?.messages || []

  // 加载知识库文档
  useEffect(() => {
    if (connected && publicKey && leftPanelMode === 'knowledge') {
      loadKnowledgeDocs()
    }
  }, [connected, publicKey, leftPanelMode])

  const loadKnowledgeDocs = async () => {
    if (!publicKey) return
    try {
      console.log('[知识库] 加载文档列表，钱包地址:', publicKey.toBase58())
      const data = await knowledgeApi.listDocuments(publicKey.toBase58())
      console.log('[知识库] 文档列表:', data.documents)
      setKnowledgeDocs(data.documents || [])
    } catch (error) {
      console.error('[知识库] 加载文档列表失败:', error)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !publicKey) return

    console.log('[知识库] 开始上传文件:', file.name, '钱包地址:', publicKey.toBase58())
    setUploading(true)
    try {
      const result = await knowledgeApi.upload(file, publicKey.toBase58())
      console.log('[知识库] 上传成功:', result)
      await loadKnowledgeDocs()
    } catch (error) {
      console.error('[知识库] 上传失败:', error)
    } finally {
      setUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleDeleteDoc = async (docId: string) => {
    if (!publicKey) return
    try {
      await knowledgeApi.deleteDocument(docId, publicKey.toBase58())
      await loadKnowledgeDocs()
    } catch (error) {
      console.error('Failed to delete document:', error)
    }
  }

  // 自动滚动到底部（仅在有消息时）
  useEffect(() => {
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages.length])

  // 创建新对话
  const createNewConversation = () => {
    const conversationId = crypto.randomUUID()
    const newConv: Conversation = {
      id: conversationId,
      title: '新对话',
      messages: [],
      sessionId: '',
      timestamp: '刚刚',
    }
    setConversations((prev) => [newConv, ...prev])
    setActiveConversationId(conversationId)
    activeIdRef.current = conversationId
  }

  const handleSend = useCallback(async () => {
    const currentActiveId = activeIdRef.current
    if (!inputMessage.trim() || isLoading || !currentActiveId) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    }

    // 添加用户消息到当前对话
    setConversations((prev) =>
      prev.map((conv) => {
        if (conv.id !== currentActiveId) return conv
        return {
          ...conv,
          messages: [...conv.messages, userMessage],
          title: conv.messages.length === 0 ? inputMessage.slice(0, 20) : conv.title,
          timestamp: '刚刚',
        }
      })
    )

    const currentInput = inputMessage
    setInputMessage('')
    setIsLoading(true)

    // 先创建一个空的 AI 消息用于流式更新
    const aiMessageId = (Date.now() + 1).toString()
    const aiMessage: Message = {
      id: aiMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    }

    setConversations((prev) =>
      prev.map((conv) => {
        if (conv.id !== currentActiveId) return conv
        return { ...conv, messages: [...conv.messages, aiMessage] }
      })
    )

    try {
      const currentConv = conversations.find((c) => c.id === currentActiveId)
      const walletAddress = connected && publicKey ? publicKey.toBase58() : ''

      console.log('[AI对话] 发送消息:', {
        message: currentInput,
        wallet_address: walletAddress,
        session_id: currentConv?.sessionId || '',
      })

      chatApi.sendMessageStream(
        {
          message: currentInput,
          wallet_address: walletAddress,
          session_id: currentConv?.sessionId || '',
        },
        {
          onToken: (token) => {
            // 收到首个 token 时关闭加载状态
            setIsLoading(false)
            // 逐字更新 AI 消息内容
            setConversations((prev) =>
              prev.map((conv) => {
                if (conv.id !== currentActiveId) return conv
                return {
                  ...conv,
                  messages: conv.messages.map((msg) =>
                    msg.id === aiMessageId
                      ? { ...msg, content: msg.content + token }
                      : msg
                  ),
                }
              })
            )
          },
          onSession: (sessionId) => {
            setConversations((prev) =>
              prev.map((conv) =>
                conv.id === currentActiveId ? { ...conv, sessionId } : conv
              )
            )
          },
          onData: (result) => {
            // 更新意图和附加数据
            setConversations((prev) =>
              prev.map((conv) => {
                if (conv.id !== currentActiveId) return conv
                return {
                  ...conv,
                  messages: conv.messages.map((msg) =>
                    msg.id === aiMessageId
                      ? { ...msg, intent: result.intent, data: result.data || undefined }
                      : msg
                  ),
                }
              })
            )
          },
          onDone: () => {
            setIsLoading(false)
          },
          onError: (error) => {
            console.error('Stream error:', error)
            setConversations((prev) =>
              prev.map((conv) => {
                if (conv.id !== currentActiveId) return conv
                return {
                  ...conv,
                  messages: conv.messages.map((msg) =>
                    msg.id === aiMessageId
                      ? { ...msg, content: msg.content || '抱歉，AI 服务暂时不可用。请确保后端服务已启动。' }
                      : msg
                  ),
                }
              })
            )
            setIsLoading(false)
          },
        }
      )
    } catch (error) {
      setConversations((prev) =>
        prev.map((conv) => {
          if (conv.id !== currentActiveId) return conv
          return {
            ...conv,
            messages: conv.messages.map((msg) =>
              msg.id === aiMessageId
                ? { ...msg, content: '抱歉，AI 服务暂时不可用。请确保后端服务已启动。' }
                : msg
            ),
          }
        })
      )
      console.error('Chat API error:', error)
      setIsLoading(false)
    }
  }, [inputMessage, isLoading, connected, publicKey, conversations])

  const handleQuickAction = (text: string) => {
    setInputMessage(text)
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* 左侧：对话列表/知识库切换 */}
      <div className="flex w-80 flex-col border-r border-gray-800 bg-gray-900">
        {/* 头部：切换按钮 */}
        <div className="flex-shrink-0 border-b border-gray-800 p-4">
          <div className="mb-3 flex gap-2">
            <Button
              variant={leftPanelMode === 'knowledge' ? 'primary' : 'outline'}
              size="sm"
              className="flex flex-1 items-center justify-center"
              onClick={() => setLeftPanelMode(leftPanelMode === 'knowledge' ? 'conversations' : 'knowledge')}
            >
              <BookOpen className="h-4 w-4" />
              <span className="ml-2">{leftPanelMode === 'knowledge' ? '收起' : '知识库'}</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="flex flex-1 items-center justify-center"
              onClick={createNewConversation}
            >
              <MessageSquare className="h-4 w-4" />
              <span className="ml-2">新对话</span>
            </Button>
          </div>
        </div>

        {/* 内容区域：根据模式切换 */}
        {leftPanelMode === 'conversations' ? (
          <>
            {/* 对话列表 */}
            <div className="flex-1 overflow-y-auto">
              <div className="space-y-1 p-2">
                {conversations.map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => {
                      setActiveConversationId(conv.id)
                      activeIdRef.current = conv.id
                    }}
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
          </>
        ) : (
          <>
            {/* 知识库：上传区域 */}
            <div className="border-b border-gray-800 p-4">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.doc,.docx,.md,.txt"
                onChange={handleFileUpload}
                className="hidden"
              />
              <Button
                variant="primary"
                size="sm"
                className="flex w-full items-center justify-center"
                onClick={() => fileInputRef.current?.click()}
                disabled={!connected || uploading}
              >
                <Upload className="h-4 w-4" />
                <span className="ml-2">{uploading ? '上传中...' : '上传文档'}</span>
              </Button>
              <p className="mt-2 text-xs text-gray-500">
                支持 PDF, DOC, DOCX, MD, TXT
              </p>
            </div>

            {/* 知识库：文档列表 */}
            <div className="flex-1 overflow-y-auto p-4">
              {!connected ? (
                <div className="text-center text-sm text-gray-400">
                  请先连接钱包
                </div>
              ) : knowledgeDocs.length === 0 ? (
                <div className="text-center text-sm text-gray-400">
                  暂无文档
                </div>
              ) : (
                <div className="space-y-2">
                  {knowledgeDocs.map((doc) => (
                    <div
                      key={doc.id}
                      className="rounded-lg border border-gray-800 bg-gray-800/50 p-3"
                    >
                      <div className="mb-2 flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 flex-shrink-0 text-indigo-400" />
                            <h4 className="truncate text-sm font-medium text-white">
                              {doc.filename}
                            </h4>
                          </div>
                          <p className="mt-1 text-xs text-gray-400">
                            {doc.file_type} · {(doc.file_size / 1024).toFixed(1)} KB
                          </p>
                          <p className="mt-1 text-xs text-gray-500">
                            {new Date(doc.upload_time).toLocaleDateString('zh-CN')}
                          </p>
                        </div>
                        <button
                          onClick={() => handleDeleteDoc(doc.id)}
                          className="ml-2 text-gray-400 hover:text-red-400"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 知识库：底部信息 */}
            <div className="flex-shrink-0 border-t border-gray-800 p-4">
              <div className="text-xs text-gray-500">
                <p>已上传 {knowledgeDocs.length} 个文档</p>
                <p className="mt-1">AI 会自动使用知识库内容</p>
              </div>
            </div>
          </>
        )}
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
