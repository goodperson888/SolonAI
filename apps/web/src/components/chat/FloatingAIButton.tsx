'use client'

import { useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { ChatWindow } from './ChatWindow'

export function FloatingAIButton() {
  const [isOpen, setIsOpen] = useState(false)
  const router = useRouter()
  const pathname = usePathname()

  // 在 AI 页面隐藏悬浮球
  if (pathname === '/ai') {
    return null
  }

  return (
    <>
      {/* 悬浮球按钮 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`group fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-purple-600 text-white shadow-lg transition-all duration-300 hover:shadow-xl ${
          isOpen ? 'scale-0' : 'scale-100'
        }`}
        aria-label="打开AI助手"
      >
        <svg
          className="h-6 w-6 transition-transform group-hover:scale-110"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
          />
        </svg>

        {/* 脉动效果 */}
        <span className="absolute inset-0 animate-ping rounded-full bg-primary-500 opacity-20"></span>
      </button>

      {/* 聊天窗口 */}
      {isOpen && (
        <div className="animate-in slide-in-from-bottom-4 fixed bottom-6 right-6 z-50 flex h-[600px] w-96 flex-col overflow-hidden rounded-2xl border border-gray-700 bg-gray-800 shadow-2xl duration-300">
          {/* 头部 */}
          <div className="flex flex-shrink-0 items-center justify-between border-b border-gray-700 bg-gradient-to-r from-primary-600 to-purple-600 p-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/20">
                <svg
                  className="h-6 w-6 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-white">Solon AI 助手</h3>
                <p className="text-xs text-white/80">随时为您服务</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* 放大按钮 */}
              <button
                onClick={() => router.push('/ai')}
                className="flex h-8 w-8 items-center justify-center rounded-full transition-colors hover:bg-white/20"
                aria-label="打开完整页面"
                title="打开完整页面"
              >
                <svg
                  className="h-4 w-4 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
                  />
                </svg>
              </button>
              {/* 关闭按钮 */}
              <button
                onClick={() => setIsOpen(false)}
                className="flex h-8 w-8 items-center justify-center rounded-full transition-colors hover:bg-white/20"
                aria-label="关闭"
              >
                <svg
                  className="h-5 w-5 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </div>

          {/* 聊天内容 - 移除 Card 的高度限制 */}
          <div className="flex min-h-0 flex-1 flex-col">
            <ChatWindow />
          </div>
        </div>
      )}
    </>
  )
}
