'use client'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface MessageBubbleProps {
  message: Message
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[70%] ${isUser ? 'order-2' : 'order-1'}`}>
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
              className={`rounded-2xl px-4 py-3 ${
                isUser
                  ? 'bg-gradient-to-br from-indigo-600 to-purple-600 text-white'
                  : 'bg-gray-800 text-gray-100'
              }`}
            >
              <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
            </div>

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
