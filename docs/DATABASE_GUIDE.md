# 数据库说明

## 目标

当前项目采用双模式开发：

- 日常联调：SQLite
- 数据库开发与部署验证：Postgres

推荐流程：

1. 先用 SQLite 跑通前后端和 AI 对话链路
2. 再在本地 Docker Postgres 中验证建表、查询、写入
3. 最后将同一份 Postgres SQL 部署到 Supabase

当前阶段不做复杂 Redis 架构设计，但已完成本地 Docker Redis 接入与核心缓存落地。

更新：

- Postgres 是当前数据库开发主路径
- Redis 已接入本地 Docker 联调、健康检查和业务缓存

---

## 当前表结构

后端当前核心表一共 5 张：

- `users`
- `chat_sessions`
- `chat_messages`
- `strategies`
- `transactions`

对应的 Postgres 建表 SQL 已固化在：

- [apps/api/sql/postgres_schema.sql](../apps/api/sql/postgres_schema.sql)

这份 SQL 包含：

- `pgcrypto` 扩展
- 所有业务 `ENUM`
- 全部表结构
- 主键 / 外键
- 主要唯一约束与索引

---

## 从 develop 分支开始的 Docker 联调流程

下面这套流程适合新开发者从零开始拉取 `develop` 分支，然后用 Docker 里的 Postgres 和 Redis 做本地联调。

### 1. 拉取代码

```bash
git clone <repo-url>
cd SolonAI
git checkout develop
git pull origin develop
```

如果你已经有仓库：

```bash
cd /Users/mac-fang/projects/codex/SolonAI
git checkout develop
git pull origin develop
```

### 2. 准备 Docker Compose 环境变量

```bash
cp .env.example .env
```

这一步用于给 Docker Compose 提供默认变量，避免出现 `SOLANA_RPC_URL`、`DATABASE_URL`、`SECRET_KEY` 等变量缺失警告。

### 3. 安装前端依赖

```bash
npm install
```

### 4. 准备后端 Python 虚拟环境

```bash
cd apps/api
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel
python -m pip install -r requirements.txt
python -m pip install -r ../../services/ai-agents/requirements.txt
cd ../..
```

如果你的机器没有 `python3.11`，请先安装 Python 3.11。

### 5. 准备前后端环境变量

```bash
cp apps/web/.env.example apps/web/.env.local
cp apps/api/.env.postgres.example apps/api/.env
cp services/ai-agents/.env.example services/ai-agents/.env
```

然后按实际模型服务填写：

```bash
services/ai-agents/.env
```

### 6. 启动 Docker Postgres 和 Redis

```bash
docker compose up -d db redis
```

确认容器正常：

```bash
docker compose ps
docker compose exec redis redis-cli ping
```

Redis 正常时应返回：

```bash
PONG
```

### 7. 初始化 Postgres 表结构

```bash
cd apps/api
source .venv/bin/activate
python -m app.core.init_postgres
cd ../..
```

确认表已创建：

```bash
docker compose exec -T db psql -U solon -d solon_ai -c "\dt"
```

### 8. 启动后端 API

```bash
cd apps/api
source .venv/bin/activate
python -m uvicorn main:app --reload --port 8000
```

打开另一个终端检查健康状态：

```bash
curl http://localhost:8000/health
```

预期返回包含：

```json
{
  "status": "healthy",
  "redis": "connected"
}
```

### 9. 启动前端

```bash
cd apps/web
npm run dev
```

访问：

```text
http://localhost:3000
```

### 10. 页面联调验证

在前端 AI 助手页面发送一条消息，然后查询 Postgres：

```bash
docker compose exec -T db psql -U solon -d solon_ai -c "select session_id, title from chat_sessions order by created_at desc limit 5;"
```

```bash
docker compose exec -T db psql -U solon -d solon_ai -c "select role, content, created_at from chat_messages order by created_at desc limit 10;"
```

查询 Redis 缓存键：

```bash
docker compose exec redis redis-cli keys '*'
```

如果能看到聊天记录写入 Postgres，且调用过缓存接口后 Redis 出现类似 `risk:*`、`chat:*`、`strategy:*` 的键，说明 Docker Postgres + Redis 联调已经完成。

---

## SQLite 联调

SQLite 仍然是默认本地联调模式。

初始化：

```bash
cp apps/api/.env.sqlite.example apps/api/.env
cd apps/api
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m app.core.init_db
```

启动：

```bash
SOLON_DB_MODE=sqlite ./start.sh
```

如果你也想顺手启动本地 Redis：

```bash
docker compose up -d redis
```

---

## Postgres 本地联调

### 1. 启动 Docker Postgres

项目根目录已经提供了本地 Postgres 服务：

```bash
docker compose up -d db
```

如果要同时联调 Redis，也一起启动：

```bash
docker compose up -d db redis
```

默认连接信息：

- Host: `localhost`
- Port: `5432`
- Database: `solon_ai`
- User: `solon`
- Password: `solon_password`

### 2. 切换 API 配置

```bash
cp apps/api/.env.postgres.example apps/api/.env
```

### 3. 用 SQL 文件建表

推荐优先使用 SQL 文件，而不是只依赖 `create_all()`：

```bash
docker compose exec -T db psql -U solon -d solon_ai < apps/api/sql/postgres_schema.sql
```

也可以直接复用项目里的 Python 初始化脚本：

```bash
cd apps/api
source .venv/bin/activate
python -m app.core.init_postgres
```

### 4. 启动后端

```bash
cd apps/api
source .venv/bin/activate
python -m uvicorn main:app --reload --port 8000
```

或者直接：

```bash
SOLON_DB_MODE=postgres ./start.sh
```

### 5. 验证建表成功

```bash
docker compose exec db psql -U solon -d solon_ai -c "\dt"
```

查看某张表结构：

```bash
docker compose exec db psql -U solon -d solon_ai -c "\d+ chat_messages"
```

### 5.1 验证 Redis 连通性

后端健康检查已经接入 Redis `PING`。启动后端后执行：

```bash
curl http://localhost:8000/health
```

如果 Redis 已连接，返回中应包含：

```json
{
  "status": "healthy",
  "redis": "connected"
}
```

也可以直接从容器里检查 Redis：

```bash
docker compose exec redis redis-cli ping
```

### 5.2 当前 Redis 已接入的功能

当前后端已经把 Redis 用在这些接口上：

- 聊天会话列表缓存
- 聊天消息历史缓存
- 钱包资产查询缓存
- 策略列表缓存
- 策略详情缓存
- 风险评估缓存
- 风险预警缓存
- 风险授权列表缓存
- 风险交易历史缓存

缓存失效规则：

- 发送聊天消息后，会自动清理对应会话列表和消息历史缓存
- 生成策略后，会自动清理该钱包的策略列表缓存
- 执行策略后，会自动清理策略详情、策略列表和风险交易历史缓存

### 6. 前端页面联调到 Docker Postgres

这是推荐给团队成员直接照着走的一套完整流程，目标是让：

- 前端页面仍然访问 `http://localhost:8000`
- 后端 API 实际连接 Docker 里的 Postgres
- 页面发出的聊天消息最终写入 `users / chat_sessions / chat_messages`

#### 步骤 1：切换 API 为 Postgres 配置

```bash
cp apps/api/.env.postgres.example apps/api/.env
```

确认 `apps/api/.env` 中的数据库连接串为：

```env
DATABASE_URL=postgresql://solon:solon_password@localhost:5432/solon_ai
```

#### 步骤 2：启动 Docker Postgres

```bash
docker compose up -d db
```

#### 步骤 3：初始化 Postgres 表结构

推荐执行固化 SQL：

```bash
cd apps/api
source .venv/bin/activate
python -m app.core.init_postgres
```

#### 步骤 4：停止旧的 SQLite 后端

如果 `8000` 端口上之前跑的是 SQLite 版本后端，需要先停掉：

```bash
lsof -tiTCP:8000 -sTCP:LISTEN | xargs kill
```

#### 步骤 5：启动 Postgres 版后端

```bash
cd apps/api
source .venv/bin/activate
python -m uvicorn main:app --reload --port 8000
```

注意：

- 前端不用改地址
- [apps/web/.env.local](../apps/web/.env.local) 继续保持 `NEXT_PUBLIC_API_URL=http://localhost:8000`
- 关键是 `8000` 上现在运行的必须是 Postgres 版后端

#### 步骤 6：从页面发起真实请求

启动前端后，在 AI 助手页面发送一条新消息。

例如：

- “帮我看看我的资产情况”
- “这是一条 Postgres 联调测试”

#### 步骤 7：在 Docker Postgres 中查库确认

查看用户：

```bash
docker compose exec -T db psql -U solon -d solon_ai -c "select wallet_address from users order by created_at desc limit 5;"
```

查看会话：

```bash
docker compose exec -T db psql -U solon -d solon_ai -c "select session_id, title from chat_sessions order by created_at desc limit 5;"
```

查看消息：

```bash
docker compose exec -T db psql -U solon -d solon_ai -c "select role, content, created_at from chat_messages order by created_at desc limit 10;"
```

如果查询结果里能看到：

- 新的 `guest:...` 或真实钱包地址
- 新的 `session_id`
- 一条 `user` 消息
- 一条 `assistant` 消息

就说明页面联调已经完全切到 Docker Postgres。

#### 常见误区

1. 页面有回复，但 Postgres 没数据

通常不是写库失败，而是页面仍然连着旧的 SQLite 后端。最常见原因是：

- `apps/api/.env` 还是 SQLite
- `8000` 端口上跑的还是旧进程
- 你验证 Postgres 时用了别的端口，但前端仍然连 `8000`

2. `chat_messages` 里没有页面消息

先确认前端请求是否真的打到当前 Postgres 后端，再确认是否重启了 API 进程。

3. `docker compose` 有一堆 `WARN`

这些通常是 `docker-compose.yml` 中其他服务使用的环境变量没有设置，当前只启动 `db` 时不影响 Postgres 联调。

4. `zsh: no matches found`

多半是 SQL 命令里的引号被 shell 吃掉了。优先使用本文档中给出的整行命令，保持双引号完整。

---

## Postgres 重置命令

如果要清空并重建本地 Docker Postgres：

```bash
docker compose down -v
docker compose up -d db
docker compose exec -T db psql -U solon -d solon_ai < apps/api/sql/postgres_schema.sql
```

---

## Supabase 部署

当 Docker 本地联调验证通过后，再部署到 Supabase。

### 方式 1：Supabase SQL Editor

直接将 [apps/api/sql/postgres_schema.sql](../apps/api/sql/postgres_schema.sql) 内容复制到 Supabase SQL Editor 执行。

### 方式 2：使用连接串执行

将 `DATABASE_URL` 改为 Supabase 的 Postgres 连接串，然后使用任意 Postgres 客户端执行这份 SQL。

示例：

```bash
psql "postgresql://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres" \
  -f apps/api/sql/postgres_schema.sql
```

如果你已经把 `apps/api/.env` 切成 Supabase 的连接串，也可以直接执行：

```bash
cd apps/api
source .venv/bin/activate
python -m app.core.init_postgres
```

注意：

- 先在本地 Docker Postgres 验证成功，再推到 Supabase
- 当前后端代码已经兼容 `postgresql://...` 并会自动转成 `postgresql+asyncpg://...`
- Supabase 线上部署前，建议先备份原有数据

---

## 相关 SQL

### 查看所有表

```sql
\dt
```

### 查看聊天消息

```sql
SELECT
    cs.session_id,
    cm.role,
    cm.content,
    cm.created_at
FROM chat_messages cm
JOIN chat_sessions cs ON cm.session_id = cs.id
ORDER BY cm.created_at DESC
LIMIT 20;
```

### 查看策略记录

```sql
SELECT
    s.title,
    s.strategy_type,
    s.status,
    s.protocol_name,
    s.created_at
FROM strategies s
ORDER BY s.created_at DESC
LIMIT 20;
```

### 查看交易记录

```sql
SELECT
    t.tx_type,
    t.status,
    t.signature,
    t.created_at
FROM transactions t
ORDER BY t.created_at DESC
LIMIT 20;
```
