'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface RagSource {
  filename: string
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  ragSources?: RagSource[]
  agentStatus?: {
    agent: string
    status: 'running' | 'done'
    message: string
  }[]
}

interface MessageBubbleProps {
  message: Message
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`${isUser ? 'order-2 max-w-[70%]' : 'order-1 max-w-[92%]'}`}>
        {/* Avatar */}
        <div className="flex items-start space-x-3">
          {!isUser && (
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-600 to-purple-600">
              <span className="text-sm font-semibold text-white">AI</span>
            </div>
          )}

          {/* Message Content */}
          <div className="flex-1">
            <div
              className={`rounded-2xl ${
                isUser
                  ? 'bg-gradient-to-br from-indigo-600 to-purple-600 px-4 py-3 text-white'
                  : 'bg-gray-800 px-4 py-3 text-gray-100'
              }`}
            >
              {/* Agent Status - 显示在消息内容上方 */}
              {!isUser && message.agentStatus && message.agentStatus.length > 0 && (
                <div className="mb-2 flex items-center gap-2 text-xs text-indigo-400">
                  {message.agentStatus.map((agent, i) => (
                    <div key={i} className="flex items-center gap-1.5">
                      {agent.status === 'running' && (
                        <>
                          <svg className="h-3 w-3 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                            />
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            />
                          </svg>
                          <span>{agent.message}</span>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {isUser ? (
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
              ) : (
                <div className="prose prose-invert prose-sm max-w-none [&_h1]:mb-3 [&_h2]:mb-3 [&_h3]:mb-3 [&_ol:last-child]:mb-0 [&_ol]:mb-3 [&_p:last-child]:mb-0 [&_p]:mb-3 [&_table]:border-collapse [&_table]:border [&_table]:border-gray-600 [&_td]:border [&_td]:border-gray-600 [&_td]:px-3 [&_td]:py-2 [&_th]:border [&_th]:border-gray-600 [&_th]:bg-gray-700/50 [&_th]:px-3 [&_th]:py-2 [&_ul:last-child]:mb-0 [&_ul]:mb-3">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                </div>
              )}
            </div>

            {/* Agent Status - 移除原来在消息气泡外的显示 */}
            {!isUser && message.ragSources && message.ragSources.length > 0 && (
              <div className="mt-1.5 flex flex-wrap gap-1.5 px-2">
                {message.ragSources.map((src, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 rounded-md bg-indigo-500/10 px-2 py-0.5 text-xs text-indigo-400"
                  >
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    {src.filename}
                  </span>
                ))}
              </div>
            )}

            {/* Timestamp */}
            <p className="mt-1 px-2 text-xs text-gray-500">
              {message.timestamp.toLocaleTimeString('zh-CN', {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          </div>

          {isUser && (
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gray-700">
              <span className="text-sm text-white">👤</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
