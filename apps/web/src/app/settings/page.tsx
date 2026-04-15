'use client'

import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { useTranslation } from '@/hooks/useTranslation'

export default function SettingsPage() {
  const { t, locale, setLocale } = useTranslation()

  return (
    <div className="min-h-screen bg-gray-950 py-8">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        {/* Page Title */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">{t('settings.title')}</h1>
          <p className="mt-2 text-gray-400">管理你的账户和偏好设置</p>
        </div>

        <div className="space-y-6">
          {/* Language Settings */}
          <Card>
            <h2 className="mb-4 text-xl font-semibold text-white">{t('settings.language')}</h2>
            <div className="space-y-3">
              <button
                onClick={() => setLocale('zh')}
                className={`w-full rounded-lg border-2 p-4 text-left transition-all ${
                  locale === 'zh'
                    ? 'border-indigo-500 bg-indigo-500/10'
                    : 'border-gray-700 hover:border-gray-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-white">简体中文</p>
                    <p className="mt-1 text-sm text-gray-400">Simplified Chinese</p>
                  </div>
                  {locale === 'zh' && <span className="text-indigo-400">✓</span>}
                </div>
              </button>

              <button
                onClick={() => setLocale('en')}
                className={`w-full rounded-lg border-2 p-4 text-left transition-all ${
                  locale === 'en'
                    ? 'border-indigo-500 bg-indigo-500/10'
                    : 'border-gray-700 hover:border-gray-600'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-white">English</p>
                    <p className="mt-1 text-sm text-gray-400">英语</p>
                  </div>
                  {locale === 'en' && <span className="text-indigo-400">✓</span>}
                </div>
              </button>
            </div>
          </Card>

          {/* Notification Settings */}
          <Card>
            <h2 className="mb-4 text-xl font-semibold text-white">{t('settings.notifications')}</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-white">策略执行通知</p>
                  <p className="mt-1 text-sm text-gray-400">当策略执行时接收通知</p>
                </div>
                <label className="relative inline-flex cursor-pointer items-center">
                  <input type="checkbox" className="peer sr-only" defaultChecked />
                  <div className="peer h-6 w-11 rounded-full bg-gray-700 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-indigo-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-800"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-white">价格预警</p>
                  <p className="mt-1 text-sm text-gray-400">当资产价格大幅波动时通知</p>
                </div>
                <label className="relative inline-flex cursor-pointer items-center">
                  <input type="checkbox" className="peer sr-only" defaultChecked />
                  <div className="peer h-6 w-11 rounded-full bg-gray-700 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-indigo-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-800"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-white">风险预警</p>
                  <p className="mt-1 text-sm text-gray-400">当检测到高风险时立即通知</p>
                </div>
                <label className="relative inline-flex cursor-pointer items-center">
                  <input type="checkbox" className="peer sr-only" defaultChecked />
                  <div className="peer h-6 w-11 rounded-full bg-gray-700 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-indigo-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-800"></div>
                </label>
              </div>
            </div>
          </Card>

          {/* Security Settings */}
          <Card>
            <h2 className="mb-4 text-xl font-semibold text-white">{t('settings.security')}</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
                <div>
                  <p className="font-medium text-white">钱包地址</p>
                  <p className="mt-1 text-sm text-gray-400">未连接</p>
                </div>
                <Button variant="outline" size="sm">
                  连接钱包
                </Button>
              </div>

              <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
                <div>
                  <p className="font-medium text-white">交易确认</p>
                  <p className="mt-1 text-sm text-gray-400">每次交易前需要确认</p>
                </div>
                <label className="relative inline-flex cursor-pointer items-center">
                  <input type="checkbox" className="peer sr-only" defaultChecked />
                  <div className="peer h-6 w-11 rounded-full bg-gray-700 after:absolute after:left-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-indigo-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-indigo-800"></div>
                </label>
              </div>

              <div className="flex items-center justify-between rounded-lg bg-gray-800 p-4">
                <div>
                  <p className="font-medium text-white">最大单笔交易额</p>
                  <p className="mt-1 text-sm text-gray-400">$10,000</p>
                </div>
                <Button variant="ghost" size="sm">
                  修改
                </Button>
              </div>
            </div>
          </Card>

          {/* About */}
          <Card>
            <h2 className="mb-4 text-xl font-semibold text-white">关于</h2>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">版本</span>
                <span className="text-white">v1.0.0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">文档</span>
                <a href="#" className="text-indigo-400 hover:text-indigo-300">
                  查看文档 →
                </a>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">支持</span>
                <a href="#" className="text-indigo-400 hover:text-indigo-300">
                  联系我们 →
                </a>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
