# Solon AI 团队任务分工方案 V2（优化版）

## 一、核心管理团队

| 角色 | 成员 | 职责 |
|------|------|------|
| **项目总负责人** | goodperson | 整体进度把控、技术方向、团队协调、关键技术攻坚 |
| **项目管理 + AI开发** | christine | 项目管理、进度跟踪、AI开发支持 |
| **AI组组长** | kwok | AI智能体架构、LangGraph工作流、大模型开发 |
| **后端+区块链组长** | Arha | 后端基础设施、区块链交互层、技术架构 |

---

## 二、工作量分析

### 各模块复杂度评估

| 模块 | 复杂度 | 工作量 | 建议人数 | 原因 |
|------|--------|--------|----------|------|
| **AI 智能体层** | ⭐⭐⭐⭐⭐ | 最大 | 5-6人 | 8个Agent逻辑、LangGraph协同、Prompt工程、RAG知识库、幻觉控制 |
| **区块链交互层** | ⭐⭐⭐⭐ | 较大 | 3-4人 | Solana RPC、多个DeFi协议集成、交易构建、Gas优化 |
| **后端基础设施** | ⭐⭐⭐ | 中等 | 1-2人 | 数据库、Redis、认证、日志（相对标准化） |
| **业务模块（前端+后端API）** | ⭐⭐ | 较小 | 4-5人 | 主要是调用接口和UI展示，逻辑简单 |

### 关键洞察
✅ **你的判断完全正确**：
1. 业务模块确实不需要那么多人，主要是调用AI组和区块链组的接口
2. AI组（8个Agent）是最复杂的，需要最多人力
3. 区块链组（多协议集成）也比较复杂，需要足够人力

---

## 三、系统架构图与人员分配

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          用户界面层                                    │
│                      (Next.js + React)                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐│
│  │ 资产诊断页面  │  │ 策略生成页面  │  │ 风控监控页面  │  │ AI对话页面││
│  │  (offset)   │  │   (Young)    │  │   (Lucky)    │  │(Fortune) ││
│  │              │  │              │  │              │  │   (CC)   ││
│  │ • 资产总览   │  │ • 策略生成   │  │ • 风控审计   │  │ • 聊天窗口││
│  │ • 盈亏分析   │  │ • 策略详情   │  │ • 交易历史   │  │ • 会话管理││
│  │ • 风险诊断   │  │ • 交易确认   │  │ • 实时预警   │  │ • 流式响应││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                 ↓ HTTP REST API
┌─────────────────────────────────────────────────────────────────────┐
│                        后端 API 层                                    │
│                      (FastAPI + Python)                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  业务组负责：简单的 API 路由，调用 AI 组接口                    │  │
│  │  • /api/assets/*      → DataAggregationAgent                 │  │
│  │  • /api/strategy/*    → StrategyAgent + ExecutionAgent       │  │
│  │  • /api/risk/*        → RiskAgent                            │  │
│  │  • /api/chat/*        → IntentAgent + ExplanationAgent       │  │
│  │  • /api/monitoring/*  → MonitoringAgent                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  基础设施（Arha 负责）                                         │  │
│  │  • PostgreSQL 数据库  • Redis 缓存  • JWT 认证  • 日志系统    │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                          ↓ Python 函数调用
┌─────────────────────────────────────────────────────────────────────┐
│                      AI 智能体层（最复杂）                             │
│                   (LangGraph + 大模型 API)                           │
│                      【AI 组：5人】                                   │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │                    LangGraph 工作流 (kwok)                      ││
│  │  全局状态管理 • Agent协同 • 错误重试 • 人机在回路               ││
│  └────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ IntentAgent  │  │StrategyAgent │  │ExecutionAgent│              │
│  │   (kwok)     │  │   (kwok)     │  │   (kwok)     │              │
│  │              │  │              │  │              │              │
│  │ • 意图理解   │  │ • 策略建模   │  │ • 交易路径   │              │
│  │ • 参数提取   │  │ • 收益测算   │  │ • 指令生成   │              │
│  │ • 多轮对话   │  │ • 风险评级   │  │ • Gas估算    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │DataAggregation│ │ RiskAgent    │  │MonitoringAgent│             │
│  │   (dean)     │  │  (snowy)     │  │   (dean)     │              │
│  │              │  │              │  │              │              │
│  │ • 多源聚合   │  │ • 黑名单匹配 │  │ • 实时监控   │              │
│  │ • 数据清洗   │  │ • 协议审计   │  │ • 异常检测   │              │
│  │ • 实时更新   │  │ • 风险评级   │  │ • 预警推送   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐                                 │
│  │Explanation   │  │Validation    │                                 │
│  │ Agent        │  │ Agent        │                                 │
│  │ (christine)  │  │ (christine)  │                                 │
│  │              │  │              │                                 │
│  │ • 通俗化解读 │  │ • 结果校验   │                                 │
│  │ • 可视化报告 │  │ • 幻觉识别   │                                 │
│  └──────────────┘  └──────────────┘                                 │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │  大模型 API (Alex)          RAG 知识库 (snowy)                  ││
│  │  • 豆包/通义千问对接        • 协议文档库                         ││
│  │  • Prompt 工程              • 风险规则库                         ││
│  │  • 流式响应                 • 策略规则库                         ││
│  └────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                          ↓ Python 函数调用
┌─────────────────────────────────────────────────────────────────────┐
│                      区块链交互层（较复杂）                            │
│                    (Solana SDK + DeFi 协议)                          │
│                      【区块链组：4人】                                 │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │              Solana RPC 客户端 (Arha)                           ││
│  │  • 获取资产  • 交易历史  • 广播交易  • 交易状态  • 节点容错     ││
│  └────────────────────────────────────────────────────────────────┘│
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Jupiter     │  │  MarginFi    │  │  Kamino      │              │
│  │  聚合交易     │  │  借贷协议     │  │  流动性挖矿   │              │
│  │   (Jack)     │  │  (arvin)     │  │  (arvin)     │              │
│  │              │  │              │  │              │              │
│  │ • 交易报价   │  │ • APY查询    │  │ • 金库信息   │              │
│  │ • 最优路径   │  │ • 存取款     │  │ • 存取款     │              │
│  │ • 滑点控制   │  │ • 健康因子   │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Raydium     │  │  Orca        │  │ 交易构建工具  │              │
│  │  流动性挖矿   │  │  流动性挖矿   │  │  (arvin)     │              │
│  │   (Jack)     │  │  (FuRong)    │  │              │              │
│  │              │  │              │  │              │              │
│  │ • 池子信息   │  │ • 池子信息   │  │ • 签名解析   │              │
│  │ • 添加流动性 │  │ • 交易构建   │  │ • Gas估算    │              │
│  │ • 无常损失   │  │              │  │ • 批量打包   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │              链上数据聚合 (FuRong)                               ││
│  │  • 多协议APY聚合  • 实时价格  • 数据缓存  • 更新调度            ││
│  └────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
                          Solana 区块链
```

### 人员分配与工作量对比

```
                    goodperson (项目总负责人)
                    christine (项目管理)
                            |
        ┌───────────────────┼───────────────────┐
        |                   |                   |
    AI 组 (5人)        区块链组 (4人)       业务组 (5人)
        |                   |                   |
   ┌────┴────┐         ┌────┴────┐        ┌────┴────┐
   |         |         |         |        |         |
 kwok组长   dean    Arha组长   arvin   offset   Young
christine  snowy     Jack    FuRong    Lucky   Fortune
  Alex                                         CC
                                              QC(机动)
```

### 工作量分析

| 层级 | 复杂度 | 人数 | 主要工作 |
|------|--------|------|----------|
| **AI 智能体层** | ⭐⭐⭐⭐⭐ | 5人 | 8个Agent逻辑、LangGraph协同、Prompt工程、RAG知识库、幻觉控制 |
| **区块链交互层** | ⭐⭐⭐⭐ | 4人 | Solana RPC、5个DeFi协议集成、交易构建、Gas优化 |
| **后端API层** | ⭐⭐ | 5人 | 简单路由，调用AI组和区块链组接口，数据转换 |
| **前端UI层** | ⭐⭐ | 5人 | 页面开发、组件封装、API调用、数据展示 |

---

## 四、优化后的分工方案

### 核心原则
1. **重兵投入核心**：AI组和区块链组投入最多人力
2. **业务组精简**：业务模块1-2人足够，快速迭代
3. **灵活调配**：业务组完成后可以支援AI组和区块链组

---

## 四、详细任务分工

### 【AI 智能体组】kwok 组长 - 5-6人（最大工作量）

**组长**：kwok
**核心成员**：dean、christine、snowy、Alex
**技术支持**：goodperson（关键节点参与）

#### 为什么需要5-6人？
- 8个Agent，每个Agent都有复杂的逻辑
- LangGraph多智能体协同流程
- Prompt工程和调优（需要大量测试）
- RAG知识库搭建（4个库：协议文档、风险规则、策略规则、用户定制）
- 幻觉控制、容错重试、结果校验
- 与区块链组和业务组的接口对接

#### Agent 分工（按复杂度分配）

**kwok 负责（3个核心Agent + LangGraph）**：
- [ ] **IntentAgent** - 意图理解（复杂度⭐⭐⭐⭐）
  - 自然语言理解
  - 意图分类（资产查询/策略生成/风控审计/交易执行）
  - 参数提取与验证
  - 歧义澄清逻辑
  - 多轮对话上下文管理

- [ ] **StrategyAgent** - 策略生成（复杂度⭐⭐⭐⭐⭐）
  - 策略建模（保守/稳健/进取）
  - 收益测算（需要复杂的金融计算）
  - 风险评级
  - 步骤拆解
  - 回测验证
  - 与区块链组对接获取实时APY

- [ ] **ExecutionAgent** - 执行协调（复杂度⭐⭐⭐⭐）
  - 交易路径优化
  - 交易指令生成
  - Gas 费估算
  - 签名解析
  - 交易上链状态跟踪
  - 与区块链组深度对接

- [ ] **LangGraph 工作流**（复杂度⭐⭐⭐⭐⭐）
  - 全局状态管理
  - Agent 协同流程
  - 错误重试机制
  - 人机在回路设计
  - 流程可视化

**dean 负责（2个Agent）**：
- [ ] **DataAggregationAgent** - 链上数据聚合（复杂度⭐⭐⭐⭐）
  - 多源数据聚合（Solana RPC、Helius、DeFi协议）
  - 数据清洗与标准化
  - 实时更新机制
  - 异常数据告警
  - 与区块链组对接

- [ ] **MonitoringAgent** - 监控与预警（复杂度⭐⭐⭐）
  - 策略实时监控
  - 异常检测
  - 收益跟踪
  - 预警推送
  - 调仓建议生成

**christine 负责（2个Agent + 项目管理）**：
- [ ] **ExplanationAgent** - 自然语言解读（复杂度⭐⭐⭐）
  - 专业内容通俗化
  - 可视化报告生成
  - 多轮对话
  - 上下文记忆

- [ ] **ValidationAgent** - 结果校验（复杂度⭐⭐⭐⭐）
  - 结果准确性校验
  - 幻觉识别（关键！）
  - 合规校验
  - 格式标准化
  - 重写指令生成

- [ ] **项目管理**
  - 每日进度跟踪
  - 风险识别与上报
  - 会议组织
  - 文档整理

**snowy 负责（1个Agent + RAG知识库）**：
- [ ] **RiskAgent** - 风控审计（复杂度⭐⭐⭐⭐⭐）
  - 黑名单匹配
  - 协议安全审计
  - 授权风险检测
  - 交易风险评级
  - 合规校验
  - 实时风险数据更新

- [ ] **RAG 知识库搭建**（复杂度⭐⭐⭐⭐）
  - 协议文档库（Solana、Jupiter、MarginFi等）
  - 风险规则库（黑名单、rug pull项目）
  - 策略规则库（DeFi策略标准）
  - 向量数据库配置（Milvus/Pinecone）
  - 知识库自动更新机制

**Alex 负责（大模型API对接 + Prompt工程）**：
- [ ] **大模型 API 对接**（复杂度⭐⭐⭐）
  - 豆包/通义千问 API 集成
  - API 容错与重试
  - 流式响应处理
  - Token 计数与成本优化

- [ ] **Prompt 工程**（复杂度⭐⭐⭐⭐）
  - 为每个Agent设计最优Prompt
  - Few-shot示例设计
  - Chain-of-Thought引导
  - 输出格式约束
  - Prompt测试与优化

**goodperson 支持（关键节点）**：
- [ ] AI架构设计评审
- [ ] 关键Agent逻辑评审
- [ ] 幻觉控制方案设计
- [ ] 性能优化指导

**AI组提供接口**（Python 函数）：
```python
# services/ai-agents/agents/intent.py
class IntentAgent:
    def understand_intent(message: str, context: dict) -> Intent

# services/ai-agents/agents/data_aggregation.py
class DataAggregationAgent:
    def aggregate_assets(wallet_address: str) -> AssetData

# services/ai-agents/agents/strategy.py
class StrategyAgent:
    def generate_strategy(request: StrategyRequest) -> Strategy

# services/ai-agents/agents/execution.py
class ExecutionAgent:
    def build_transaction(strategy: Strategy) -> Transaction

# services/ai-agents/agents/risk.py
class RiskAgent:
    def audit_transaction(tx_data: dict) -> RiskResult
    def audit_strategy(strategy: Strategy) -> RiskResult

# services/ai-agents/agents/monitoring.py
class MonitoringAgent:
    def monitor_strategy(strategy_id: str) -> MonitoringResult

# services/ai-agents/agents/explanation.py
class ExplanationAgent:
    def generate_response(intent: Intent, data: any) -> str

# services/ai-agents/agents/validation.py
class ValidationAgent:
    def validate_result(result: any, expected_type: str) -> ValidationResult
```

**交付物**：
- 8个 Agent 完整实现
- LangGraph 工作流
- RAG 知识库
- 大模型API封装
- AI 层接口文档
- 单元测试

---

### 【区块链交互组】Arha 组长 - 3-4人（较大工作量）

**组长**：Arha
**核心成员**：arvin、Jack、FuRong

#### 为什么需要3-4人？
- Solana RPC 封装（复杂）
- 多个DeFi协议集成（Jupiter、MarginFi、Raydium、Orca、Kamino）
- 交易构建、签名、Gas优化
- 实时数据获取和缓存
- 错误处理和重试机制

#### 任务分工

**Arha 负责（Solana RPC + 后端基础设施）**：
- [ ] **Solana RPC 客户端封装**（复杂度⭐⭐⭐⭐）
  - `get_wallet_assets()` - 获取钱包资产
  - `get_transaction_history()` - 获取交易历史
  - `get_token_balance()` - 获取代币余额
  - `broadcast_transaction()` - 广播交易
  - `get_transaction_status()` - 查询交易状态
  - `simulate_transaction()` - 交易模拟
  - RPC节点容错切换

- [ ] **后端基础设施**（复杂度⭐⭐⭐）
  - 数据库设计与初始化
  - Redis 缓存策略
  - JWT 认证与鉴权
  - API 限流
  - 日志系统
  - 部署配置

**arvin 负责（MarginFi + Kamino + 交易构建）**：
- [ ] **MarginFi 借贷协议集成**（复杂度⭐⭐⭐⭐）
  - `get_apy()` - 获取借贷 APY
  - `build_deposit_transaction()` - 构建存款交易
  - `build_withdraw_transaction()` - 构建取款交易
  - `get_user_positions()` - 获取用户仓位
  - `calculate_health_factor()` - 计算健康因子

- [ ] **Kamino 流动性挖矿集成**（复杂度⭐⭐⭐）
  - `get_vault_info()` - 获取金库信息
  - `build_deposit_transaction()` - 构建存款交易
  - `build_withdraw_transaction()` - 构建取款交易

- [ ] **交易构建工具**（复杂度⭐⭐⭐⭐）
  - 交易签名解析
  - Gas 费估算
  - 交易优先级费用计算
  - 交易批量打包

**Jack 负责（Jupiter + Raydium）**：
- [ ] **Jupiter 聚合交易集成**（复杂度⭐⭐⭐⭐）
  - `get_quote()` - 获取交易报价
  - `build_swap_transaction()` - 构建交易指令
  - `get_route()` - 获取最优路径
  - `get_price_impact()` - 计算价格影响
  - 滑点控制

- [ ] **Raydium 流动性挖矿集成**（复杂度⭐⭐⭐）
  - `get_pool_info()` - 获取池子信息
  - `build_add_liquidity_transaction()` - 添加流动性
  - `build_remove_liquidity_transaction()` - 移除流动性
  - `calculate_impermanent_loss()` - 计算无常损失

**FuRong 负责（Orca + 数据聚合）**：
- [ ] **Orca 流动性挖矿集成**（复杂度⭐⭐⭐）
  - `get_pool_info()` - 获取池子信息
  - `build_swap_transaction()` - 构建交易
  - `build_add_liquidity_transaction()` - 添加流动性

- [ ] **链上数据聚合**（复杂度⭐⭐⭐）
  - 多协议APY数据聚合
  - 实时价格数据获取
  - 数据缓存策略
  - 数据更新调度

**区块链组提供接口**（Python 模块）：
```python
# services/blockchain/solana_client.py
class SolanaClient:
    def get_wallet_assets(address: str) -> dict
    def get_transaction_history(address: str, limit: int) -> list
    def broadcast_transaction(signed_tx: str) -> str
    def simulate_transaction(tx: str) -> SimulationResult

# services/blockchain/jupiter_client.py
class JupiterClient:
    def get_quote(input_mint: str, output_mint: str, amount: int) -> Quote
    def build_swap_transaction(quote: Quote, user_pubkey: str) -> Transaction

# services/blockchain/marginfi_client.py
class MarginFiClient:
    def get_apy(token: str) -> float
    def build_deposit_transaction(token: str, amount: int, user: str) -> Transaction
    def get_user_positions(user: str) -> list

# services/blockchain/raydium_client.py
class RaydiumClient:
    def get_pool_info(pool_id: str) -> PoolInfo
    def build_add_liquidity_transaction(pool_id: str, amounts: dict) -> Transaction

# services/blockchain/orca_client.py
class OrcaClient:
    def get_pool_info(pool_id: str) -> PoolInfo
    def build_swap_transaction(input_mint: str, output_mint: str, amount: int) -> Transaction
```

**交付物**：
- 完整的区块链交互 SDK
- 后端基础设施
- 数据库设计文档
- 单元测试覆盖率 > 80%
- API 文档

---

### 【业务模块组】4个模块 - 5人（精简配置）

业务组主要负责前端页面 + 后端 API，**逻辑简单，主要是调用AI组和区块链组的接口**。

#### 模块1：钱包接入 + 资产诊断
**负责人**：offset（1人独立负责）

**前端任务**：
- [ ] Dashboard 页面开发（资产总览、盈亏分析、风险诊断 3个Tab）
- [ ] 资产卡片组件优化
- [ ] 统计卡片组件开发
- [ ] 资产图表可视化

**后端任务**：
- [ ] `/api/assets/list` - 调用 `DataAggregationAgent.aggregate_assets()`
- [ ] `/api/assets/diagnose` - 调用 `DataAggregationAgent` + `RiskAgent`
- [ ] `/api/assets/pnl` - 调用 `DataAggregationAgent`

**工作量评估**：⭐⭐（1人，5天）

---

#### 模块2：策略生成 + 执行
**负责人**：Young（1人独立负责）

**前端任务**：
- [ ] 策略生成页面开发
- [ ] 策略卡片组件优化
- [ ] 策略详情页面
- [ ] 交易确认弹窗

**后端任务**：
- [ ] `/api/strategy/generate` - 调用 `StrategyAgent.generate_strategy()`
- [ ] `/api/strategy/execute` - 调用 `ExecutionAgent.build_transaction()`
- [ ] `/api/strategy/list` - 数据库查询
- [ ] `/api/strategy/detail/:id` - 数据库查询

**工作量评估**：⭐⭐（1人，5天）

---

#### 模块3：风控审计 + 监控预警
**负责人**：Lucky（1人独立负责）

**前端任务**：
- [ ] 风控审计页面开发
- [ ] 交易历史页面开发
- [ ] 风险预警通知组件
- [ ] 监控仪表盘

**后端任务**：
- [ ] `/api/risk/audit` - 调用 `RiskAgent.audit_transaction()`
- [ ] `/api/monitoring/alerts` - 调用 `MonitoringAgent.monitor_strategy()`
- [ ] WebSocket 实时推送

**工作量评估**：⭐⭐（1人，5天）

---

#### 模块4：AI 对话 + 自然语言交互
**负责人**：Fortune + CC（2人）

**前端任务**（Fortune）：
- [ ] AI 对话页面开发
- [ ] 聊天窗口组件优化
- [ ] 会话历史管理
- [ ] 全局 AI 悬浮球优化

**后端任务**（CC）：
- [ ] `/api/chat/message` - 调用 `IntentAgent` + `ExplanationAgent`
- [ ] `/api/chat/sessions` - 数据库查询
- [ ] 流式响应（SSE）

**工作量评估**：⭐⭐⭐（2人，5天）

---

#### 剩余成员（QC）
**角色**：机动支援
**任务**：
- 前期：协助业务组开发
- 中期：支援AI组或区块链组（哪边进度慢支援哪边）
- 后期：测试、文档、部署

---

## 五、人员分配总结

| 组别 | 组长 | 成员 | 人数 | 工作量 |
|------|------|------|------|--------|
| **AI 组** | kwok | dean、christine、snowy、Alex | 5人 | ⭐⭐⭐⭐⭐ |
| **区块链组** | Arha | arvin、Jack、FuRong | 4人 | ⭐⭐⭐⭐ |
| **业务组** | - | offset、Young、Lucky、Fortune、CC | 5人 | ⭐⭐ |
| **机动支援** | - | QC | 1人 | - |
| **管理层** | goodperson | christine（兼任） | 2人 | - |

**总计**：17人
- AI组：5人（最大工作量）
- 区块链组：4人（较大工作量）
- 业务组：5人（较小工作量，可快速完成）
- 机动支援：1人
- 管理层：2人（goodperson + christine兼任）

---

## 六、开发时间表（2周 MVP）

### 第0周：准备阶段（2天）
**时间**：Day 1-2
**所有人参与**：
- [ ] 接口规范评审（HTTP API + Python 函数接口）
- [ ] 数据库设计评审
- [ ] 开发环境搭建
- [ ] Git 分支策略培训
- [ ] 任务认领与分工确认

---

### 第1周：基础设施 + 核心开发

#### Day 3-5（前3天）：基础设施优先
**区块链组（Arha、arvin、Jack、FuRong）**：
- [ ] Solana RPC 客户端完成（Arha）
- [ ] Jupiter 集成完成（Jack）
- [ ] MarginFi 集成完成（arvin）
- [ ] 后端基础设施完成（Arha）
- [ ] 提供基础 SDK 给 AI 组使用

**AI 组（kwok、dean、christine、snowy、Alex）**：
- [ ] LangGraph 基础框架搭建（kwok）
- [ ] 大模型 API 对接完成（Alex）
- [ ] RAG 知识库初版完成（snowy）
- [ ] 开始开发核心 Agent

**业务组（offset、Young、Lucky、Fortune、CC）**：
- [ ] 前端基础组件开发
- [ ] 后端 API 框架搭建
- [ ] Mock 数据准备

#### Day 6-9（后4天）：核心功能开发
**AI 组**：
- [ ] IntentAgent 完成（kwok）
- [ ] StrategyAgent 50%（kwok）
- [ ] DataAggregationAgent 完成（dean）
- [ ] ExplanationAgent 完成（christine）
- [ ] RiskAgent 50%（snowy）
- [ ] Prompt 工程 50%（Alex）

**区块链组**：
- [ ] Raydium 集成完成（Jack）
- [ ] Orca 集成完成（FuRong）
- [ ] Kamino 集成完成（arvin）
- [ ] 交易构建工具完成（arvin）

**业务组**：
- [ ] 模块1 完成 80%（offset）
- [ ] 模块2 完成 80%（Young）
- [ ] 模块3 完成 80%（Lucky）
- [ ] 模块4 完成 50%（Fortune + CC）

**第1周末检查点**：
- 基础设施 100% 完成
- AI 组 50% 完成
- 区块链组 80% 完成
- 业务组 70% 完成

---

### 第2周：功能完善 + 联调测试

#### Day 10-12（前3天）：功能完善
**AI 组**：
- [ ] 所有 Agent 100% 完成
- [ ] LangGraph 工作流完成
- [ ] RAG 知识库完善
- [ ] Prompt 优化完成

**区块链组**：
- [ ] 所有协议集成 100% 完成
- [ ] 性能优化
- [ ] 单元测试

**业务组**：
- [ ] 所有模块 100% 完成
- [ ] UI/UX 优化

#### Day 13-14（中2天）：集成联调
**所有人参与**：
- [ ] 前后端联调
- [ ] AI 层与区块链层联调
- [ ] 端到端测试
- [ ] Bug 修复

#### Day 15-16（后2天）：测试与优化
**所有人参与**：
- [ ] Devnet 测试网全流程验证
- [ ] 性能优化
- [ ] 文档完善
- [ ] 部署到测试环境

**第2周末交付**：
- MVP 版本上线
- 所有核心功能可用
- 文档齐全

---

## 七、关键优势

### 相比 V1 版本的改进

| 方面 | V1 版本 | V2 版本（优化） | 改进 |
|------|---------|----------------|------|
| **AI 组人数** | 3人 | 5人 | ✅ 增加2人，匹配最大工作量 |
| **区块链组人数** | 3人 | 4人 | ✅ 增加1人，匹配较大工作量 |
| **业务组人数** | 9人 | 5人 | ✅ 减少4人，避免人力浪费 |
| **业务组配置** | 每模块3人 | 每模块1-2人 | ✅ 更合理，业务逻辑简单 |
| **人力分配** | 平均分配 | 按工作量分配 | ✅ 重兵投入核心模块 |

### 核心优势
1. **重兵投入核心**：AI组5人、区块链组4人，确保最复杂的部分有足够人力
2. **业务组精简**：业务模块1-2人足够，避免人力浪费
3. **灵活调配**：业务组完成后可以支援AI组和区块链组
4. **责任清晰**：每个模块有明确的负责人

---

## 八、风险控制

### 技术风险
- **AI 幻觉问题**：ValidationAgent 二次校验 + RAG 知识库约束
- **区块链层延期**：第1周前3天必须完成基础SDK
- **API 调用失败**：容错重试机制 + 备用节点

### 协作风险
- **接口不一致**：第0周统一接口规范
- **代码冲突**：分支隔离 + 频繁合并

### 进度风险
- **AI组进度慢**：业务组完成后支援AI组
- **某个Agent延期**：其他成员支援

---

## 九、成功标准

### MVP 版本交付标准
- [ ] 用户可以连接钱包
- [ ] 用户可以查看资产诊断
- [ ] 用户可以生成策略
- [ ] 用户可以执行策略（Devnet）
- [ ] 用户可以进行风控审计
- [ ] 用户可以使用 AI 对话
- [ ] 所有核心 API 可用
- [ ] 代码覆盖率 > 60%
- [ ] 文档齐全

### 质量标准
- [ ] 无 P0/P1 级别 Bug
- [ ] API 响应时间 < 2s
- [ ] 前端页面加载时间 < 3s
- [ ] AI 幻觉率 < 5%
- [ ] 代码通过 ESLint/Prettier/Black 检查

---

**最后更新**：2024-04-16
**文档维护**：goodperson

**V2 版本核心改进**：
- ✅ AI 组从 3人 增加到 5人（匹配最大工作量）
- ✅ 区块链组从 3人 增加到 4人（匹配较大工作量）
- ✅ 业务组从 9人 减少到 5人（避免人力浪费）
- ✅ 每个业务模块从 3人 减少到 1-2人（更合理）

Let's build something amazing! 🚀
