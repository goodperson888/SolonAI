# 资产诊断页面 (Asset Diagnosis) 开发计划

基于 `origin/test/trigger-ci` 分支的团队分工设定，资产诊断页面属于**用户界面层**的核心模块，包含三大子视图：**资产总览 (Overview)**、**盈亏分析 (PnL)** 和 **风险诊断 (Risk)**。

以下是从零开始实现该页面的标准开发计划（Plan）和实施路径。

## 1. 架构与技术选型
- **框架路由**：Next.js 14 App Router (目录 `apps/web/src/app/analysis/` 或复用 `dashboard/`)
- **UI & 样式**：Tailwind CSS + 现有的基础 UI 组件（Button, Card 等）
- **图表可视化**：引入 `recharts` 或 `echarts`（用于渲染资产占比饼图、盈亏折线图、风险雷达图）
- **数据请求**：使用 `@tanstack/react-query` 结合项目中已有的 `apiClient` 进行异步状态管理（Loading/Error/Success）

## 2. 页面结构与路由设计
页面采用 **"顶层概览 + 底部 Tab 切换"** 的结构：
- **顶层区域**：展示全局核心指标（总资产、24h涨跌、综合健康分），复用 `StatCard` 组件。
- **Tab 切换区**：
  1. **资产总览 (Asset Overview)**：
     - 资产分布饼图（Token 占比）
     - 资产列表（复用 `AssetCard`，展示代币、余额、价值、变化率）
  2. **盈亏分析 (PnL Analysis)**：
     - 历史收益率折线图 / 柱状图
     - 累计收益、胜率等进阶指标卡片
  3. **风险诊断 (Risk Diagnosis)**：
     - 风险维度雷达图（流动性、集中度、波动率等）
     - AI 风险评估报告（文本展示区，展示底层 RiskAgent 生成的洞察）
     - 风险预警列表（高危资产提示）

## 3. 核心组件拆分 (Component Breakdown)
需要在 `apps/web/src/components/analysis/` 目录下新增以下业务组件：
- `AnalysisTabs.tsx`：Tab 导航容器
- `OverviewTab.tsx`：包含 `AssetDistributionChart` 和资产列表
- `PnLTab.tsx`：包含 `PnLTrendChart` 和盈亏数据统计
- `RiskTab.tsx`：包含 `RiskRadarChart` 和 `AIReportPanel`

## 4. 数据模型与接口定义 (TypeScript Interfaces)
在 `apps/web/src/types/` 或对应页面下定义数据结构，以便与后端 FastAPI 交互：

```typescript
// 资产数据
export interface Asset {
  symbol: string;
  balance: number;
  valueUsd: number;
  change24h: number;
}

// 盈亏数据
export interface PnLRecord {
  date: string;
  profitUsd: number;
  roi: number;
}

// 风险诊断报告
export interface RiskDiagnosis {
  healthScore: number;
  dimensions: { category: string; score: number }[];
  warnings: string[];
  aiAdvice: string;
}
```

## 5. 分步实施路径 (Implementation Steps)

### Phase 1: 基础骨架与依赖安装
1. 安装图表库依赖：`npm install recharts` (或对应图表库)。
2. 在 `apps/web/src/app/analysis/page.tsx` 中搭建基础 Layout 和 Tab 切换逻辑。

### Phase 2: 静态 UI 与图表开发 (Mock Driven)
1. 完善静态 Mock 数据（`mockAssets.ts` 补充盈亏和风险时间序列数据）。
2. 开发 `OverviewTab`，实现资产分布饼图和列表。
3. 开发 `PnLTab`，实现收益折线图。
4. 开发 `RiskTab`，实现风险雷达图和 AI 诊断结果卡片。

### Phase 3: 真实数据接入 (API Integration)
1. 在 `apps/web/src/lib/api/` 中封装后端请求函数：
   - `getAssetList(walletAddress)` -> 对应后端 `/api/v1/assets/list`
   - `getPnLHistory(walletAddress)` -> 对应后端 `/api/v1/assets/pnl`
   - `getRiskDiagnosis(walletAddress)` -> 对应后端 `/api/v1/assets/diagnose`
2. 在页面组件中引入 `useQuery` (React Query) 替换 Mock 数据，增加 Skeleton Loading 和骨架屏。

### Phase 4: 联调与优化 (Polish)
1. 配合后端开发人员（负责 `DataAggregationAgent` 和 `RiskAgent` 的同学）进行接口联调。
2. 处理钱包未连接状态的空状态（Empty State）提示。
3. 响应式移动端适配和暗色模式（Dark Mode）测试。
