# Infra 数据模型开发规范

## 1. 文档目标

本文档面向 `infra`、后端和后续负责数据库建模的同学，定义 Solon AI 在 MVP 阶段的关系数据库模型规范与 Redis 缓存设计。

适用技术栈：
- 后端：FastAPI (Python 3.11+)
- 关系数据库：PostgreSQL (Supabase 免费版)
- 缓存：Redis (Upstash 免费版)
- 认证：JWT
- 部署：Railway 免费版

约束边界：
- 本文档只定义设计方案，不直接落地 SQLAlchemy Model、Alembic Migration 或 API 代码。
- 业务核心关系模型范围限定为 `users`、`strategies`、`transactions`。
- Redis 仅作为派生缓存、会话态和幂等控制层，不作为业务真相源。

---
## 2. 与现有项目的对齐原则

结合当前仓库实现：
- `apps/api/app/core/database.py` 已采用 `SQLAlchemy AsyncSession + declarative_base`
- `apps/api/app/core/security.py` 已采用 JWT
- `apps/api/app/core/config.py` 已预留 `DATABASE_URL`、`REDIS_URL`
- `docs/ARCHITECTURE.md` 已给出三张核心业务表：用户表、策略表、交易表

因此后续实现建议遵循：
- SQLAlchemy 2.x 风格优先
- 异步数据库会话沿用当前 `AsyncSessionLocal`
- 所有模型命名使用单数类名、复数表名
- 所有迁移按“枚举/扩展 -> 表 -> 索引 -> 外键”的顺序执行

---

## 3. 总体设计原则

### 3.1 数据分层

- PostgreSQL 是业务真相源，保存用户、策略、交易的长期事实数据
- Redis 是性能层，保存短期缓存、会话态、幂等键和热点风险数据
- AI Agent 输出中的复杂结构使用 `JSONB` 持久化，但页面和接口高频筛选字段必须冗余为独立列

### 3.2 字段规范

- 主键统一使用 `UUID`
- 时间字段统一使用 `TIMESTAMPTZ`
- 金额统一使用 `NUMERIC`
- 状态字段统一使用受控枚举，不直接依赖自由文本
- 所有表统一包含：
  - `id`
  - `created_at`
  - `updated_at`

### 3.3 免费版平台约束

- Supabase 免费版连接数有限，避免过度复杂触发器与实时订阅
- Railway 免费环境连接池应保守设置，建议后续实现中控制数据库连接上限
- Upstash Redis 更适合轻量缓存，不适合大对象或长期正文存储

---

## 4. 枚举字典规范

### 4.1 风险偏好 `risk_level`

固定枚举：
- `conservative`
- `balanced`
- `aggressive`

说明：
- `users.risk_level` 表示用户长期风险偏好
- `strategies.risk_level` 表示策略本身风险等级，默认使用同一字典，方便联动筛选

### 4.2 用户状态 `user_status`

推荐枚举：
- `active`
- `disabled`
- `deleted`

说明：
- MVP 不建议物理删除用户
- `deleted` 表示业务软删除或停用

### 4.3 策略状态 `strategy_status`

推荐枚举：
- `draft`
- `generated`
- `approved`
- `rejected`
- `expired`
- `executed`

说明：
- `generated` 表示 Agent 已生成策略
- `approved` 表示用户确认可执行
- `executed` 表示已有实际执行记录

### 4.4 交易状态 `transaction_status`

推荐枚举：
- `draft`
- `prepared`
- `signed`
- `submitted`
- `confirmed`
- `failed`
- `expired`

说明：
- 该状态流转与 `docs/ARCHITECTURE.md` 中“生成交易 -> 钱包签名 -> 上链提交 -> 监听状态”的链路保持一致

### 4.5 交易类型 `tx_type`

推荐枚举：
- `swap`
- `lend`
- `withdraw`
- `stake`
- `unstake`
- `rebalance`

---

## 5. 核心关系模型

## 5.1 `users` 用户表

### 定位

保存用户账户、登录身份、风险偏好与个性化配置。

### 字段定义

| 字段名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | `UUID` | PK | 用户主键 |
| `wallet_address` | `VARCHAR(64)` | `UNIQUE NOT NULL` | Solana 钱包地址，主登录标识 |
| `email` | `VARCHAR(255)` | `UNIQUE NULL` | 可选，预留后台或扩展登录 |
| `password_hash` | `VARCHAR(255)` | `NULL` | 可选，仅邮箱登录场景使用 |
| `risk_level` | `VARCHAR(32)` | `NOT NULL` | 用户风险偏好 |
| `status` | `VARCHAR(32)` | `NOT NULL DEFAULT 'active'` | 用户状态 |
| `preferences` | `JSONB` | `NOT NULL DEFAULT '{}'` | 用户个性化偏好 |
| `last_login_at` | `TIMESTAMPTZ` | `NULL` | 最近登录时间 |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | 更新时间 |

### 索引

- 唯一索引：`wallet_address`
- 唯一索引：`email`
- 普通索引：`risk_level`
- 可选索引：`status`

### `preferences` 示例

```json
{
  "preferred_tokens": ["USDC", "SOL"],
  "blocked_protocols": ["ProtocolX"],
  "notification_channels": ["app"],
  "language": "zh-CN"
}
```

### 设计说明

- 钱包登录是主路径，因此 `wallet_address` 必须唯一且可高频检索
- JWT 的 `sub` 默认建议使用 `user.id`
- 敏感偏好不写入 JWT，只保存在数据库或 Redis 会话态中

---

## 5.2 `strategies` 策略表

### 定位

保存 Agent 生成的结构化策略、收益测算结果和风险审计摘要。

### 字段定义

| 字段名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | `UUID` | PK | 策略主键 |
| `user_id` | `UUID` | `FK NOT NULL` | 所属用户 |
| `strategy_type` | `VARCHAR(32)` | `NOT NULL` | 策略类型 |
| `status` | `VARCHAR(32)` | `NOT NULL` | 策略状态 |
| `input_token` | `VARCHAR(32)` | `NOT NULL` | 输入代币 |
| `output_token` | `VARCHAR(32)` | `NULL` | 输出代币 |
| `input_amount` | `NUMERIC(38,18)` | `NULL` | 输入金额 |
| `estimated_apy` | `NUMERIC(10,4)` | `NULL` | 预估 APY |
| `risk_level` | `VARCHAR(32)` | `NOT NULL` | 策略风险等级 |
| `protocol_name` | `VARCHAR(64)` | `NULL` | 主要推荐协议 |
| `title` | `VARCHAR(255)` | `NOT NULL` | 策略标题 |
| `summary` | `TEXT` | `NULL` | 摘要描述 |
| `steps` | `JSONB` | `NOT NULL DEFAULT '[]'` | 执行步骤 |
| `strategy_payload` | `JSONB` | `NOT NULL DEFAULT '{}'` | 完整策略结构化结果 |
| `risk_assessment` | `JSONB` | `NOT NULL DEFAULT '{}'` | 风险审计摘要 |
| `expires_at` | `TIMESTAMPTZ` | `NULL` | 失效时间 |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | 更新时间 |

### 索引

- 组合索引：`(user_id, created_at DESC)`
- 普通索引：`status`
- 普通索引：`strategy_type`
- 普通索引：`protocol_name`

### `steps` 示例

```json
[
  {
    "step": 1,
    "action": "deposit",
    "protocol": "MarginFi",
    "token": "USDC",
    "amount": "1000"
  },
  {
    "step": 2,
    "action": "monitor",
    "trigger": "apy_drop_below_4_percent"
  }
]
```

### `strategy_payload` 示例

```json
{
  "strategy_name": "USDC稳健借贷策略",
  "recommendations": [
    {
      "protocol": "MarginFi",
      "allocation_ratio": 0.7,
      "estimated_apy": 4.2
    }
  ],
  "assumptions": {
    "market": "neutral",
    "holding_period_days": 30
  },
  "agent_version": "strategy-agent-v1"
}
```

### `risk_assessment` 示例

```json
{
  "overall_risk": "low",
  "risk_factors": [
    "protocol_smart_contract_risk",
    "apy_volatility"
  ],
  "validation_status": "passed",
  "checked_at": "2026-04-17T12:00:00Z"
}
```

### 设计说明

- `strategy_payload` 用于保存 Agent 原始结构化结果，方便后续解释、审计和二次执行
- 高查询字段单独冗余为普通列，避免页面列表完全依赖 `JSONB` 检索
- 不建议把策略计算结果仅放 Redis，防止策略审计链丢失

---

## 5.3 `transactions` 交易表

### 定位

保存策略执行过程中的交易草稿、签名、提交结果与链上确认状态。

### 字段定义

| 字段名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | `UUID` | PK | 交易主键 |
| `user_id` | `UUID` | `FK NOT NULL` | 所属用户 |
| `strategy_id` | `UUID` | `FK NOT NULL` | 来源策略 |
| `signature` | `VARCHAR(128)` | `UNIQUE NULL` | 链上签名 |
| `status` | `VARCHAR(32)` | `NOT NULL` | 交易状态 |
| `tx_type` | `VARCHAR(32)` | `NOT NULL` | 交易类型 |
| `chain` | `VARCHAR(16)` | `NOT NULL DEFAULT 'solana'` | 链标识 |
| `from_token` | `VARCHAR(32)` | `NULL` | 输入代币 |
| `to_token` | `VARCHAR(32)` | `NULL` | 输出代币 |
| `amount` | `NUMERIC(38,18)` | `NULL` | 金额 |
| `slippage_bps` | `INTEGER` | `NULL` | 滑点基点 |
| `tx_payload` | `JSONB` | `NOT NULL DEFAULT '{}'` | 交易构建结果 |
| `simulation_result` | `JSONB` | `NOT NULL DEFAULT '{}'` | 模拟执行结果 |
| `error_message` | `TEXT` | `NULL` | 错误信息 |
| `submitted_at` | `TIMESTAMPTZ` | `NULL` | 提交时间 |
| `confirmed_at` | `TIMESTAMPTZ` | `NULL` | 确认时间 |
| `created_at` | `TIMESTAMPTZ` | `NOT NULL` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | `NOT NULL` | 更新时间 |

### 索引

- 组合索引：`(user_id, created_at DESC)`
- 普通索引：`strategy_id`
- 唯一索引：`signature`
- 普通索引：`status`

### `tx_payload` 示例

```json
{
  "route": "jupiter",
  "instructions_count": 3,
  "expected_out_amount": "998.2",
  "priority_fee": "low",
  "raw_message_version": "v0"
}
```

### `simulation_result` 示例

```json
{
  "simulated": true,
  "success": true,
  "warnings": ["slippage_close_to_threshold"],
  "estimated_fee_sol": 0.00001
}
```

### 设计说明

- `signature` 在草稿期允许为空，因此唯一约束应允许 `NULL`
- 一个策略允许产生多笔交易记录，例如重试、分步执行、再平衡
- 交易状态流转建议为：
  - `draft -> prepared -> signed -> submitted -> confirmed`
  - 异常分支：`prepared/submitted -> failed`
  - 超时分支：`draft/prepared -> expired`

---

## 6. 表关系与约束规范

### 6.1 关系定义

- `users 1:N strategies`
- `users 1:N transactions`
- `strategies 1:N transactions`

### 6.2 外键策略

- `strategies.user_id -> users.id`
- `transactions.user_id -> users.id`
- `transactions.strategy_id -> strategies.id`

### 6.3 删除与审计策略

- 默认不做级联硬删除
- 推荐通过业务状态停用用户或策略，而不是直接物理删除
- 原因：
  - 交易与风控审计链需要长期保留
  - AI 输出和链上执行行为需要可追踪

---

## 7. SQLAlchemy Model 开发规范

### 7.1 建模建议

- 使用 SQLAlchemy 2.x declarative 风格
- 所有表统一继承当前项目中的 `Base`
- 每个模型显式声明：
  - `__tablename__`
  - 主键
  - 索引
  - 外键
  - `nullable`
  - 默认值

### 7.2 时间字段建议

- `created_at`：数据库默认值 `now()`
- `updated_at`：数据库默认值 `now()`，更新时自动刷新
- 应用层和数据库层保持 UTC 存储

### 7.3 JSONB 使用原则

适合使用 `JSONB` 的内容：
- Agent 完整输出
- 执行步骤
- 风险摘要
- 用户偏好
- 模拟执行明细

不适合只放 `JSONB` 的内容：
- 钱包地址
- 风险等级
- 状态
- 协议名
- 交易签名
- 高频筛选和排序字段

### 7.4 Migration 规范

后续迁移建议顺序：
1. 创建扩展与枚举
2. 创建基础表 `users`
3. 创建从表 `strategies`
4. 创建从表 `transactions`
5. 创建索引
6. 回填或初始化数据

避免事项：
- 在单个迁移中混入过多数据回填逻辑
- 在免费版数据库上使用复杂触发器链
- 对大 `JSONB` 字段建立过多表达式索引

---

## 8. JWT 与认证数据规范

### 8.1 JWT 载荷原则

JWT 中仅保留最小身份声明，例如：

```json
{
  "sub": "user_uuid",
  "wallet_address": "wallet_optional",
  "exp": 1713350000
}
```

不建议放入 JWT 的数据：
- 完整用户偏好
- 风险黑名单
- 自定义投资规则
- 大量权限信息

### 8.2 会话更新建议

- 用户登录成功后刷新 `last_login_at`
- Redis 中写入短期会话态
- 数据库存长期身份事实，Redis 存临时授权与黑名单状态

---

## 9. Redis 内存数据库设计方案

## 9.1 设计原则

- Redis 只做缓存与运行态辅助
- Key 统一命名：

```text
solon:{env}:{domain}:{id_or_hash}
```

示例：
- `solon:prod:auth:session:{user_id}`
- `solon:prod:strategy:{strategy_id}`

### 9.2 缓存对象设计

#### 1. 用户会话

- Key：`solon:prod:auth:session:{user_id}`
- Value：用户会话快照
- TTL：30 分钟到 24 小时

示例：

```json
{
  "user_id": "uuid",
  "wallet_address": "xxxx",
  "login_at": "2026-04-17T12:00:00Z",
  "scopes": ["basic"]
}
```

#### 2. JWT 黑名单 / 登出态

- Key：`solon:prod:auth:deny:{jti}`
- Value：`1`
- TTL：与 token 剩余生命周期一致

#### 3. 钱包资产快照

- Key：`solon:prod:assets:{wallet_address}`
- TTL：15 到 60 秒
- 用途：避免重复请求链上 RPC

#### 4. 策略详情缓存

- Key：`solon:prod:strategy:{strategy_id}`
- TTL：5 分钟
- 用途：策略详情页和执行确认页读取

#### 5. 用户策略列表缓存

- Key：`solon:prod:user:{user_id}:strategies:{page}`
- TTL：5 分钟
- 用途：策略列表分页缓存

#### 6. 风控热点名单缓存

- Key：`solon:prod:risk:blacklist:{address}`
- TTL：1 到 5 分钟
- 用途：高频地址黑名单快速判定

#### 7. 幂等键

- Key：`solon:prod:idempotency:{request_hash}`
- TTL：10 分钟
- 用途：避免短时间重复生成策略或重复提交交易

---

## 9.3 Redis 失效策略

### 策略相关

- 创建策略后删除：
  - `solon:prod:user:{user_id}:strategies:*`
- 更新策略后删除：
  - `solon:prod:strategy:{strategy_id}`
  - `solon:prod:user:{user_id}:strategies:*`

### 交易相关

- 交易状态变化后删除：
  - `solon:prod:strategy:{strategy_id}`
  - 交易详情缓存（后续如新增）
  - 用户策略列表缓存

### 风险同步相关

- 链上黑名单同步后按地址级刷新：
  - `solon:prod:risk:blacklist:{address}`

### 资产相关

- 钱包资产不做强一致缓存，采用短 TTL 自然过期

---

## 10. 典型业务流校验场景

### 场景 1：新用户钱包登录

1. 前端完成钱包签名验证
2. 后端按 `wallet_address` 查找 `users`
3. 用户不存在则创建一条 `users`
4. 生成 JWT，`sub=user.id`
5. Redis 写入 `auth:session:{user_id}`

### 场景 2：生成策略

1. 用户请求到达 `/strategy/generate`
2. LangGraph/Agent 生成结构化策略
3. `strategies` 保存普通字段、`steps`、`strategy_payload`、`risk_assessment`
4. 失效用户策略列表缓存

### 场景 3：交易执行

1. 根据策略生成交易草稿
2. 写入 `transactions(status=draft/prepared)`
3. 钱包签名后更新 `signature` 与状态
4. 上链提交后更新 `submitted_at`
5. 监听确认后更新 `confirmed_at` 与状态

### 场景 4：黑名单同步

1. 链上安全数据源同步最新黑名单
2. 数据库存权威事实
3. Redis 刷新热点地址缓存
4. 风险检查优先查 Redis，未命中回源数据库

---

## 11. 实施建议

### 实施建议

- 先实现三张核心表与基础索引
- 再补策略和交易的 `JSONB` 结构规范
- 最后接入 Redis 缓存与失效逻辑

---

## 12. 最终推荐

对于当前 Solon AI 的基础设施层，推荐采用：
- PostgreSQL 作为唯一业务真相源
- Redis 作为短期缓存、会话和幂等控制层
- 三张核心表先稳定支撑用户、策略、交易主链路
- 所有 Agent 输出必须可落库、可审计、可回溯

