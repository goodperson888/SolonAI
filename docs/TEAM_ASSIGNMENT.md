# Solon AI 团队任务分工方案

## 一、核心管理团队

| 角色 | 成员 | 职责 |
|------|------|------|
| **项目总负责人** | goodperson | 整体进度把控、技术方向、团队协调、大模型开发 |
| **项目管理 + AI开发** | christine | 项目管理、进度跟踪、大模型开发 |
| **AI组组长** | kwok | AI智能体架构、LangGraph工作流、大模型开发 |
| **后端+区块链组长** | Arha | 后端基础设施、区块链交互层、技术架构 |

## 二、团队成员技能矩阵

| 成员 | 前端 | 后端 | AI/大模型 | 区块链 | 综合能力 | 分组 |
|------|------|------|-----------|--------|----------|------|
| **goodperson** | ✅ | ✅ | ✅ | ✅ | 项目总负责人 | 管理层 |
| **christine** | ❌ | ❌ | ✅ | ✅ | 项目管理+AI | 管理层 |
| **kwok** | ✅ | ✅ | ✅ | ✅ | AI组长 | AI组 |
| **Arha** | ✅ | ✅ | ✅ | ✅ | 后端+区块链组长 | 基础设施组 |
| snowy | ✅ | ✅ | ✅ | ✅ | 全栈+AI | 业务组 |
| Alex | ✅ | ✅ | ✅ | ✅ | 全栈+AI | 业务组 |
| dean | ✅ | ✅ | ✅ | ✅ | 全栈+AI | AI组 |
| arvin | ✅ | ✅ | ✅ | ✅ | 全栈+AI | 基础设施组 |
| Jack | ✅ | ✅ | ✅ | ✅ | 全栈+AI | 基础设施组 |
| FuRong | ✅ | ✅ | ✅ | ✅ | 全栈+AI | 业务组 |
| cc | ✅ | ✅ | ✅ | ✅ | 全栈+AI | 业务组 |
| offset | ✅ | ✅ | ❌ | ✅ | 全栈 | 业务组 |
| Young | ✅ | ✅ | ❌ | ✅ | 全栈 | 业务组 |
| Lucky | ✅ | �� | ❌ | ✅ | 全栈 | 业务组 |
| Fortune | ✅ | ✅ | ❌ | ✅ | 全栈 | 业务组 |
| CC | ✅ | ✅ | ❌ | ✅ | 全栈 | 业务组 |
| QC | ✅ | ✅ | ❌ | ✅ | 全栈 | 业务组 |

**总计**：17人
- 管理层：2人（goodperson、christine）
- AI组：3人（kwok组长 + dean + christine兼任）
- 基础设施组：3人（Arha组长 + arvin + Jack）
- 业务组：9人（snowy、Alex、FuRong、cc、offset、Young、Lucky、Fortune、CC、QC）

### 组织架构图
```
                    goodperson（项目总负责人）
                            |
        ┌───────────────────┼───────────────────┐
        |                   |                   |
   christine            kwok组长            Arha组长
  (项目管理)           (AI组)          (基础设施组)
        |                   |                   |
        |              ┌────┴────┐         ┌────┴────┐
        |            dean    christine    arvin    Jack
        |                   (兼任)
        |
        └─────────────────┬─────────────────────────┐
                          |                         |
                    业务模块组                  业务模块组
                          |                         |
        ┌─────────────────┼─────────────┐          |
        |                 |             |          |
    snowy组          Alex组        FuRong组      cc
   (模块1)          (模块2)        (模块3)     (模块4)
        |                 |             |
  offset,Young    Lucky,Fortune    CC,QC
```

---

## 三、核心分工策略

### 分工原则
1. **分层架构**：AI组、基础设施组、业务组三层分工
2. **AI组独立**：kwok带领AI组专注8个Agent开发和LangGraph工作流
3. **基础设施优先**：Arha带领基础设施组第一周必须完成后端+区块链
4. **业务组并行**：4个业务模块同时开工，最大化效率

### 数据流架构
```
前端（Next.js）
    ↓ HTTP REST API
后端 API（FastAPI）
    ↓ Python 函数调用
AI 智能体层（LangGraph）← kwok组负责
    ↓ Python 函数调用
区块链交互层（Solana SDK）← Arha组负责
    ↓
链上数据/执行交易
```

---

## 四、详细任务分工

### 【AI 智能体组】kwok 组长，专注 AI 层

**组长**：kwok
**组员**：dean、christine（兼项目管理）
**技术支持**：goodperson（总负责人，参与关键 AI 开发）

**核心职责**：
- 8个 AI Agent 的完整开发
- LangGraph 多智能体工作流搭建
- 大模型 API 对接（豆包/通义千问）
- RAG 知识库搭建
- AI 层接口设计与文档

#### Agent 分工

**kwok 负责（4个）**：
- [ ] **IntentAgent** - 意图理解
  - 自然语言理解
  - 意图分类（资产查询/策略生成/风控审计/交易执行）
  - 参数提取与验证
  - 歧义澄清逻辑

- [ ] **StrategyAgent** - 策略生成
  - 策略建模（保守/稳健/进取）
  - 收益测算
  - 风险评级
  - 步骤拆解
  - 回测验证

- [ ] **ExecutionAgent** - 执行协调
  - 交易路径优化
  - 交易指令生成
  - Gas 费估算
  - 签名解析
  - 交易上链状态跟踪

- [ ] **LangGraph 工作流**
  - 全局状态管理
  - Agent 协同流程
  - 错误重试机制
  - 人机在回路设计

**dean 负责（2个）**：
- [ ] **DataAggregationAgent** - 链上数据聚合
  - 多源数据聚合（Solana RPC、Helius、DeFi协议）
  - 数据清洗与标准化
  - 实时更新机制
  - 异常数据告警

- [ ] **MonitoringAgent** - 监控与预警
  - 策略实时监控
  - 异常检测
  - 收益跟踪
  - 预警推送
  - 调仓建议生成

**christine 负责（2个 + 项目管理）**：
- [ ] **ExplanationAgent** - 自然语言解读
  - 专业内容通俗化
  - 可视化报告生成
  - 多轮对话
  - 上下文记忆

- [ ] **ValidationAgent** - 结果校验
  - 结果准确性校验
  - 幻觉识别
  - 合规校验
  - 格式标准化
  - 重写指令生成

- [ ] **项目管理**
  - 每日进度跟踪
  - 风险识别与上报
  - 会议组织
  - 文档整理

**goodperson 支持（关键节点）**：
- [ ] **RiskAgent** - 风控审计（与 Alex 协作）
  - 黑名单匹配
  - 协议安全审计
  - 授权风险检测
  - 交易风险评级
  - 合规校验

- [ ] **RAG 知识库搭建**
  - 协议文档库
  - 风险规则库
  - 策略规则库
  - 向量数据库配置（Milvus/Pinecone）

**AI组提供接口**（Python 函数）：
```python
# services/ai-agents/agents/intent.py
class IntentAgent:
    def understand_intent(message: str) -> Intent

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
    def generate_response(intent: Intent) -> str

# services/ai-agents/agents/validation.py
class ValidationAgent:
    def validate_result(result: any) -> ValidationResult
```

**交付物**：
- 8个 Agent 完整实现
- LangGraph 工作流
- RAG 知识库
- AI 层接口文档
- 单元测试

---

### 【基础设施组】Arha 组长，后端 + 区块链

**组长**：Arha
**组员**：arvin、Jack

**核心职责**：
- 后端 API 基础设施
- 区块链交互层
- 数据库设计
- 部署与运维

#### 后端基础设施（Arha 负责）

**核心任务**（第1周必须完成）：

- [ ] **数据库设计与初始化**
  - 用户表（users）
  - 资产表（assets）
  - 策略表（strategies）
  - 交易记录表（transactions）
  - 会话表（chat_sessions）
  - 消息表（chat_messages）
  - 监控预警表（alerts）

- [ ] **Redis 缓存策略**
  - 资产数据缓存（5分钟）
  - 协议 APY 缓存（10分钟）
  - 用户会话缓存
  - 限流计数器

- [ ] **认证与鉴权**
  - JWT Token 生成与验证
  - 钱包签名验证
  - API 限流（每用户 100次/分钟）
  - CORS 配置

- [ ] **日志与监控**
  - 结构化日志（JSON格式）
  - 错误日志告警
  - API 性能监控
  - 数据库慢查询监控

- [ ] **部署与 CI/CD**
  - Docker Compose 配置优化
  - GitHub Actions 优化
  - Vercel 前端部署配置
  - Railway 后端部署配置
  - 环境变量管理

#### 区块链交互层（arvin + Jack 负责）

**核心任务**（第1周必须完成）：

- [ ] **Solana RPC 客户端封装**（arvin）
  - `get_wallet_assets()` - 获取钱包资产
  - `get_transaction_history()` - 获取交易历史
  - `get_token_balance()` - 获取代币余额
  - `broadcast_transaction()` - 广播交易
  - `get_transaction_status()` - 查询交易状态

- [ ] **Jupiter 聚合交易集成**（Jack）
  - `get_quote()` - 获取交易报价
  - `build_swap_transaction()` - 构建交易指令
  - `get_route()` - 获取最优路径

- [ ] **MarginFi 借贷协议集成**（arvin）
  - `get_apy()` - 获取借贷 APY
  - `build_deposit_transaction()` - 构建存款交易
  - `build_withdraw_transaction()` - 构建取款交易
  - `get_user_positions()` - 获取用户仓位

- [ ] **Raydium 流动性挖矿集成**（Jack）
  - `get_pool_info()` - 获取池子信息
  - `build_add_liquidity_transaction()` - 添加流动性
  - `build_remove_liquidity_transaction()` - 移除流动性

- [ ] **交易构建工具**（arvin + Jack）
  - 交易签名解析
  - Gas 费估算
  - 交易模拟（simulate）

**基础设施组提供接口**（Python 模块）：
```python
# services/blockchain/solana_client.py
class SolanaClient:
    def get_wallet_assets(address: str) -> dict
    def get_transaction_history(address: str) -> list
    def broadcast_transaction(signed_tx: str) -> str

# services/blockchain/jupiter_client.py
class JupiterClient:
    def get_quote(input_mint: str, output_mint: str, amount: int) -> dict
    def build_swap_transaction(quote: dict) -> dict

# services/blockchain/marginfi_client.py
class MarginFiClient:
    def get_apy(token: str) -> float
    def build_deposit_transaction(token: str, amount: int) -> dict
```

**交付物**：
- 完整的后端基础设施
- 完整的区块链交互 SDK
- 数据库设计文档
- 单元测试覆盖率 > 80%
- API 文档

---

### 【业务模块组】4个小组，并行开发

业务组负责前端页面 + 后端 API 开发，调用 AI 组和基础设施组提供的接口。

#### 模块1：钱包接入 + 资产诊断
**负责人**：snowy（组长）
**组员**：offset、Young

**前端任务**（offset + Young）：
- [ ] Dashboard 页面开发（资产总览、盈亏分析、风险诊断 3个Tab）
- [ ] 资产卡片组件（AssetCard）优化
- [ ] 统计卡片组件（StatCard）开发
- [ ] 资产图表可视化（ECharts/Recharts）
- [ ] 钱包连接状态管理

**后端任务**（snowy）：
- [ ] `/api/assets/list` - 获取资产列表
- [ ] `/api/assets/diagnose` - 资产诊断
- [ ] `/api/assets/pnl` - 盈亏分析
- [ ] 资产数据缓存策略（Redis）
- [ ] 调用 AI 组的 `DataAggregationAgent`

**交付物**：
- 完整的资产诊断页面
- 资产相关 API 接口

---

#### 模块2：策略生成 + 执行
**负责人**：Alex（组长）
**组员**：Lucky、Fortune

**前端任务**（Lucky + Fortune）：
- [ ] 策略生成页面开发
- [ ] 策略卡片组件（StrategyCard）优化
- [ ] 策略详情页面（/strategy/[id]）
- [ ] 交易确认弹窗组件
- [ ] 策略执行进度展示

**后端任务**（Alex）：
- [ ] `/api/strategy/generate` - 生成策略
- [ ] `/api/strategy/execute` - 执行策略
- [ ] `/api/strategy/list` - 策略列表
- [ ] `/api/strategy/detail/:id` - 策略详情
- [ ] 策略执行状态跟踪
- [ ] 调用 AI 组的 `StrategyAgent` 和 `ExecutionAgent`

**交付物**：
- 完整的策略生成和执行页面
- 策略相关 API 接口

---

#### 模块3：风控审计 + 监控预警
**负责人**：FuRong（组长）
**组员**：CC、QC

**前端任务**（CC + QC）：
- [ ] 风控审计页面开发
- [ ] 交易历史页面开发
- [ ] 风险预警通知组件
- [ ] 监控仪表盘
- [ ] 授权管理页面

**后端任务**（FuRong）：
- [ ] `/api/risk/audit` - 风控审计
- [ ] `/api/risk/blacklist` - 黑名单查询
- [ ] `/api/monitoring/alerts` - 监控预警
- [ ] `/api/monitoring/strategy/:id` - 策略监控
- [ ] WebSocket 实时推送
- [ ] 调用 AI 组的 `RiskAgent` 和 `MonitoringAgent`

**交付物**：
- 完整的风控和监控页面
- 风控相关 API 接口

---

#### 模块4：AI 对话 + 自然语言交互
**负责人**：cc（组长）
**组员**：无（cc 独立负责前后端）

**前端任务**（cc）：
- [ ] AI 对话页面开发（/ai）
- [ ] 聊天窗口组件优化
- [ ] 消息气泡组件优化
- [ ] 会话历史管理
- [ ] 快捷操作按钮
- [ ] 全局 AI 悬浮球优化

**后端任务**（cc）：
- [ ] `/api/chat/message` - 发送消息
- [ ] `/api/chat/sessions` - 会话列表
- [ ] `/api/chat/history/:sessionId` - 会话历史
- [ ] 会话状态管理
- [ ] 流式响应（SSE）
- [ ] 调用 AI 组的 `IntentAgent` 和 `ExplanationAgent`

**交付物**：
- 完整的 AI 对话页面
- 对话相关 API 接口

---

## 四、开发时间表（2周 MVP）

### 第0周：准备阶段（2天，所有人参与）
**时间**：Day 1-2

**所有人一起做**：
- [ ] 接口规范评审（HTTP API + Python 函数接口）
- [ ] 数据库设计评审
- [ ] 开发环境搭建（克隆项目、安装依赖）
- [ ] Git 分支策略培训
- [ ] 代码规范培训（ESLint、Prettier、Black）
- [ ] 任务认领与分工确认

**产出**：
- 接口文档（Swagger/OpenAPI）
- 数据库设计文档
- 开发环境就绪

---

### 第1周：基础设施 + 核心功能开发
**时间**：Day 3-9

#### Day 3-5（前3天）：基础设施优先
**区块链组（arvin、Jack）**：
- [ ] Solana RPC 客户端完成
- [ ] Jupiter 集成完成
- [ ] MarginFi 集成完成
- [ ] Raydium 集成完成
- [ ] 提供基础 SDK 给其他组使用

**基础设施组（Arha）**：
- [ ] 数据库初始化完成
- [ ] Redis 缓存配置完成
- [ ] 认证系统完成
- [ ] 日志系统完成

#### Day 6-9（后4天）：业务模块并行开发
**所有业务组同时开工**：

**模块1组（snowy、offset、Young）**：
- [ ] 前端：Dashboard 页面 50%（offset + Young）
- [ ] 后端：资产 API 完成（snowy）
- [ ] 调用 AI 组的 DataAggregationAgent

**模块2组（Alex、Lucky、Fortune）**：
- [ ] 前端：策略页面 50%（Lucky + Fortune）
- [ ] 后端：策略 API 完成（Alex）
- [ ] 调用 AI 组的 StrategyAgent 和 ExecutionAgent

**模块3组（FuRong、CC、QC）**：
- [ ] 前端：风控页面 50%（CC + QC）
- [ ] 后端：风控 API 完成（FuRong）
- [ ] 调用 AI 组的 RiskAgent 和 MonitoringAgent

**模块4组（cc）**：
- [ ] 前端：AI 对话页面 50%（cc）
- [ ] 后端：对话 API 完成（cc）
- [ ] 调用 AI 组的 IntentAgent 和 ExplanationAgent

**第1周末检查点**：
- 基础设施 100% 完成
- 业务模块 50% 完成
- 所有 API 接口可调用

---

### 第2周：功能完善 + 联调测试
**时间**：Day 10-16

#### Day 10-12（前3天）：功能完善
**所有业务组**：
- [ ] 前端页面 100% 完成
- [ ] 后端 API 100% 完成
- [ ] AI Agent 100% 完成
- [ ] 单元测试编写

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
- [ ] UI/UX 优化
- [ ] 文档完善
- [ ] 部署到测试环境

**第2周末交付**：
- MVP 版本上线
- 所有核心功能可用
- 文档齐全

---

## 五、协作规范

### Git 分支策略
```
main（主分支，保护）
  ↓
develop（开发分支，保护）
  ↓
feature/module1-assets（模块1功能分支）
feature/module2-strategy（模块2功能分支）
feature/module3-risk（模块3功能分支）
feature/module4-ai-chat（模块4功能分支）
feature/blockchain-base（区块链基础设施分支）
feature/backend-infra（后端基础设施分支）
```

### 提交规范
```bash
# 功能开发
git commit -m "feat(module1): add asset diagnosis page"

# Bug 修复
git commit -m "fix(module2): fix strategy generation error"

# 文档更新
git commit -m "docs: update API documentation"
```

### 代码审查
- 所有 PR 必须经过至少 1 人审查
- 组长负责审查本组成员的代码
- 跨组接口变更需要双方组长确认

### 每日站会（15分钟）
- 时间：每天早上 10:00
- 内容：
  - 昨天完成了什么
  - 今天计划做什么
  - 遇到什么阻塞

### 周会（1小时）
- 时间：每周五下午 5:00
- 内容：
  - 本周进度回顾
  - 下周计划
  - 问题讨论

---

## 六、关键里程碑

| 时间 | 里程碑 | 负责人 | 验收标准 |
|------|--------|--------|----------|
| Day 2 | 接口规范确定 | goodperson、kwok、Arha | 接口文档评审通过 |
| Day 5 | 基础设施完成 | Arha、arvin、Jack | SDK 可用，其他组可以调用 |
| Day 7 | AI 组 50% | kwok、dean、christine | 4个核心 Agent 可用 |
| Day 9 | 业务模块 50% | snowy、Alex、FuRong、cc | 前端页面可访问，API 可调用 |
| Day 12 | 所有模块 100% | 所有组长 | 所有功能开发完成 |
| Day 14 | 联调完成 | goodperson | 端到端流程跑通 |
| Day 16 | MVP 上线 | goodperson | 测试环境部署成功 |

---

## 七、风险控制

### 技术风险
- **区块链层延期**：影响所有业务模块
  - 缓解措施：第1周前3天必须完成，组长每日检查进度

- **AI 幻觉问题**：影响用户体验
  - 缓解措施：ValidationAgent 二次校验，RAG 知识库约束

- **API 调用失败**：影响系统稳定性
  - 缓解措施：容错重试机制，备用 API

### 协作风险
- **接口不一致**：导致联调失败
  - 缓解措施：第0周统一接口规范，变更需双方确认

- **代码冲突**：影响开发效率
  - 缓解措施：分支隔离，频繁合并 develop

### 进度风险
- **某个模块延期**：影响整体进度
  - 缓解措施：每日站会跟进，及时调配人力

---

## 八、联系方式

### 管理层
| 角色 | 成员 | 职责 |
|------|------|------|
| 项目总负责人 | goodperson | 整体进度把控、技术方向、团队协调 |
| 项目管理 | christine | 项目管理、进度跟踪、会议组织 |

### 技术组
| 组别 | 组长 | 成员 | 沟通渠道 |
|------|------|------|----------|
| **AI 组** | kwok | dean、christine | Telegram群 / 飞书群 |
| **基础设施组** | Arha | arvin、Jack | Telegram群 / 飞书群 |
| **模块1组（资产）** | snowy | offset、Young | Telegram群 / 飞书群 |
| **模块2组（策略）** | Alex | Lucky、Fortune | Telegram群 / 飞书群 |
| **模块3组（风控）** | FuRong | CC、QC | Telegram群 / 飞书群 |
| **模块4组（AI对话）** | cc | 无 | Telegram群 / 飞书群 |

**紧急联系**：
- 技术问题：在 GitHub Issues 提问，@相关组长
- 阻塞问题：在群里 @goodperson 或 @christine
- 进度问题：联系 christine（项目管理）
- 架构问题：联系 goodperson（技术总负责人）

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
- [ ] 代码通过 ESLint/Prettier/Black 检查
- [ ] 所有 PR 经过代码审查

---

**最后更新**：2024-04-16
**文档维护**：goodperson

如有任何问题，请在 GitHub Issues 提出或在群里讨论。

Let's build something amazing! 🚀
