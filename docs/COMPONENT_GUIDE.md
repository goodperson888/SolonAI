# 前端组件使用指南

## 📚 目录

- [快速开始](#快速开始)
- [基础组件](#基础组件)
- [业务组件](#业务组件)
- [页面示例](#页面示例)
- [国际化](#国际化)
- [样式规范](#样式规范)

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd apps/web
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

---

## 🧩 基础组件

### Button 按钮

位置: `src/components/ui/Button.tsx`

**Props:**
- `variant`: 'primary' | 'secondary' | 'outline' | 'ghost'
- `size`: 'sm' | 'md' | 'lg'
- `children`: React.ReactNode
- 其他原生 button 属性

**示例:**

```tsx
import { Button } from '@/components/ui/Button'

<Button variant="primary" size="lg">
  连接钱包
</Button>

<Button variant="outline" size="md">
  取消
</Button>
```

---

### Card 卡片

位置: `src/components/ui/Card.tsx`

**Props:**
- `children`: React.ReactNode
- `className`: string (可选)
- `hover`: boolean (是否启用悬停效果)

**示例:**

```tsx
import { Card } from '@/components/ui/Card'

<Card hover>
  <h3>卡片标题</h3>
  <p>卡片内容</p>
</Card>
```

---

### Input 输入框

位置: `src/components/ui/Input.tsx`

**Props:**
- `label`: string (可选)
- `error`: string (可选)
- 其他原生 input 属性

**示例:**

```tsx
import { Input } from '@/components/ui/Input'

<Input
  label="投资金额"
  type="number"
  placeholder="1000"
  error={errors.amount}
/>
```

---

## 💼 业务组件

### AssetCard 资产卡片

位置: `src/components/assets/AssetCard.tsx`

**Props:**
- `icon`: string (代币图标)
- `symbol`: string (代币符号，如 SOL)
- `name`: string (代币名称，如 Solana)
- `amount`: number (持有数量)
- `value`: number (美元价值)
- `change24h`: number (24小时涨跌幅)

**示例:**

```tsx
import { AssetCard } from '@/components/assets/AssetCard'

<AssetCard
  icon="S"
  symbol="SOL"
  name="Solana"
  amount={125.5}
  value={18825.75}
  change24h={5.2}
/>
```

---

### StrategyCard 策略卡片

位置: `src/components/strategy/StrategyCard.tsx`

**Props:**
- `name`: string (策略名称)
- `protocol`: string (协议名称)
- `expectedAPY`: number (预期年化收益率)
- `riskLevel`: 'low' | 'medium' | 'high'
- `lockPeriod`: string (锁定期)
- `steps`: string[] (操作步骤)
- `deployed`: boolean (是否已部署)
- `deployedAmount`: number (已部署金额，可选)

**示例:**

```tsx
import { StrategyCard } from '@/components/strategy/StrategyCard'

<StrategyCard
  name="USDC稳定收益策略"
  protocol="MarginFi"
  expectedAPY={8.5}
  riskLevel="low"
  lockPeriod="无锁定"
  steps={[
    '将USDC存入MarginFi',
    '获得存款凭证mUSDC',
    '自动复利',
  ]}
  deployed={true}
  deployedAmount={3000}
/>
```

---

### StatCard 统计卡片

位置: `src/components/dashboard/StatCard.tsx`

**Props:**
- `title`: string (标题)
- `value`: string | number (数值)
- `change`: number (变化百分比，可选)
- `icon`: string (图标，可选)
- `trend`: 'up' | 'down' | 'neutral' (趋势)

**示例:**

```tsx
import { StatCard } from '@/components/dashboard/StatCard'

<StatCard
  title="总资产价值"
  value="$28,675.75"
  change={3.8}
  trend="up"
  icon="💰"
/>
```

---

### ChatWindow AI聊天窗口

位置: `src/components/chat/ChatWindow.tsx`

**使用:**

```tsx
import { ChatWindow } from '@/components/chat/ChatWindow'

<ChatWindow />
```

内置功能:
- 消息列表显示
- 输入框
- 发送按钮
- 加载状态

---

## 📄 页面示例

### 创建新页面

1. 在 `src/app/` 下创建文件夹
2. 创建 `page.tsx` 文件
3. 使用已有组件构建页面

**示例: 创建一个新页面**

```tsx
// src/app/my-page/page.tsx
'use client'

import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { useTranslation } from '@/hooks/useTranslation'

export default function MyPage() {
  const { t } = useTranslation()

  return (
    <div className="min-h-screen bg-gray-950 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-white mb-8">
          我的页面
        </h1>

        <Card>
          <p className="text-white">页面内容</p>
          <Button variant="primary" className="mt-4">
            操作按钮
          </Button>
        </Card>
      </div>
    </div>
  )
}
```

---

## 🌍 国际化

### 使用翻译

```tsx
import { useTranslation } from '@/hooks/useTranslation'

function MyComponent() {
  const { t, locale, setLocale } = useTranslation()

  return (
    <div>
      <h1>{t('dashboard.title')}</h1>
      <button onClick={() => setLocale(locale === 'zh' ? 'en' : 'zh')}>
        切换语言
      </button>
    </div>
  )
}
```

### 添加新翻译

1. 编辑 `src/locales/zh.ts` (中文)
2. 编辑 `src/locales/en.ts` (英文)

```typescript
// src/locales/zh.ts
export const zh = {
  myPage: {
    title: '我的页面',
    description: '这是描述',
  },
}

// src/locales/en.ts
export const en = {
  myPage: {
    title: 'My Page',
    description: 'This is description',
  },
}
```

使用:

```tsx
{t('myPage.title')}
{t('myPage.description')}
```

---

## 🎨 样式规范

### 颜色

```tsx
// 背景色
bg-gray-950  // 最深背景
bg-gray-900  // 次深背景
bg-gray-800  // 卡片背景

// 文字颜色
text-white      // 主要文字
text-gray-400   // 次要文字
text-gray-500   // 辅助文字

// 主题色
bg-gradient-to-r from-indigo-600 to-purple-600  // 主题渐变
text-indigo-400  // 链接/强调色

// 状态色
text-green-500   // 上涨/成功
text-red-500     // 下跌/错误
text-yellow-500  // 警告
```

### 圆角

```tsx
rounded-lg   // 8px - 小元素
rounded-xl   // 12px - 卡片
rounded-2xl  // 16px - 大卡片
rounded-full // 圆形 - 头像/徽章
```

### 间距

```tsx
space-y-4  // 垂直间距 1rem
space-x-4  // 水平间距 1rem
gap-6      // Grid 间距 1.5rem
p-6        // 内边距 1.5rem
```

### 响应式

```tsx
// 移动端优先
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
  // 移动端1列，平板2列，桌面3列
</div>

// 断点
sm: 640px
md: 768px
lg: 1024px
xl: 1280px
```

---

## 📦 Mock数据

### 使用Mock数据

```tsx
import { mockAssets } from '@/data/mockAssets'
import { mockStrategies } from '@/data/mockStrategies'
import { mockMessages } from '@/data/mockMessages'

// 在组件中使用
function MyComponent() {
  return (
    <div>
      {mockAssets.map(asset => (
        <AssetCard key={asset.id} {...asset} />
      ))}
    </div>
  )
}
```

### Mock数据文件

- `src/data/mockAssets.ts` - 资产数据
- `src/data/mockStrategies.ts` - 策略数据
- `src/data/mockMessages.ts` - 聊天消息数据

---

## 🔧 常见问题

### 1. 如何添加新组件？

1. 在 `src/components/` 下创建文件
2. 使用 TypeScript 定义 Props
3. 遵循现有组件的样式规范
4. 导出组件

### 2. 如何修改主题色？

编辑 `tailwind.config.js`:

```js
theme: {
  extend: {
    colors: {
      primary: {
        // 修改这里的颜色
      },
    },
  },
}
```

### 3. 如何对接后端API？

替换Mock数据为真实API调用:

```tsx
// 之前: 使用Mock数据
import { mockAssets } from '@/data/mockAssets'

// 之后: 调用API
const { data: assets } = await fetch('/api/assets')
```

---

## 📞 需要帮助？

- 查看现有页面代码: `src/app/dashboard/page.tsx`
- 查看组件实现: `src/components/`
- 参考设计规范: `docs/FRONTEND_DESIGN.md`

---

**祝开发顺利！** 🚀
