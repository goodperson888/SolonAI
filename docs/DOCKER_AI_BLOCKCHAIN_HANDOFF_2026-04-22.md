# Docker 联调与改动交接文档

更新时间：2026-04-22

本文档用于记录今天围绕 `AI agent`、`blockchain`、`apps/api`、`apps/web`、Docker 联调与 smoke test 的主要改动、验证步骤、已知问题与交接建议。

## 1. 目标与范围

今天主要完成了三类工作：

1. 修复并验证 AI agent、blockchain、前后端在 Docker 环境下的联调链路。
2. 增加可复用的 Docker smoke test。
3. 收紧部分依赖与测试逻辑，避免“假通过”。

另外，针对“页面切换后 AI 对话历史无法保留”的问题做了多轮修复尝试，但截至本文档落地时，该问题仍未确认彻底解决，建议由前端工程师继续接手。

## 2. 今天的主要代码改动

### 2.1 AI agent 相关

- [services/ai-agents/graphs/main_graph.py](/Users/mac-fang/projects/codex/SolonAI/services/ai-agents/graphs/main_graph.py:1)
  - 修复 LangGraph 节点名与状态 key 重名问题。
  - 之前 `intent` 节点名与状态字段 `intent` 冲突，会导致工作流初始化失败。

- [services/ai-agents/rag/knowledge_base.py](/Users/mac-fang/projects/codex/SolonAI/services/ai-agents/rag/knowledge_base.py:1)
  - 增加 `faiss` 不可用时的内存向量检索降级逻辑。
  - 目标是避免缺失 `faiss` 时系统知识库直接不可用。

- [services/ai-agents/requirements.txt](/Users/mac-fang/projects/codex/SolonAI/services/ai-agents/requirements.txt:1)
  - 将 AI 相关依赖收紧为当前项目实际验证过的一组版本。
  - 目的：
    - 避免 Docker 构建时 `pip` 大规模依赖回溯。
    - 消除构建阶段“告警但继续”的不确定性。
  - 当前主要 pin 的包包括：
    - `langchain==0.3.25`
    - `langchain-core==0.3.63`
    - `langchain-community==0.3.24`
    - `langchain-openai==0.3.19`
    - `langchain-text-splitters==0.3.8`
    - `langgraph==0.2.35`
    - `langgraph-checkpoint==2.1.2`
    - `langsmith==0.2.11`
    - `openai==1.109.1`
    - `faiss-cpu==1.13.2`
    - `pydantic==2.13.2`
    - `pydantic-settings==2.13.1`
    - `aiohttp==3.13.5`
    - `numpy==2.4.4`
    - `tiktoken==0.12.0`

### 2.2 API / 后端相关

- [apps/api/Dockerfile](/Users/mac-fang/projects/codex/SolonAI/apps/api/Dockerfile:1)
  - 调整 API 镜像构建逻辑，保留仓库目录结构。
  - 将 `services/ai-agents` 与 `services/blockchain` 一起复制进镜像。
  - 将 `PYTHONPATH` 调整为：
    - `/workspace/services`
    - `/workspace/services/ai-agents`
    - `/workspace/apps/api`
  - 作用：
    - API 容器内可正常 import AI agent 模块。
    - API 容器内可正常 import blockchain 模块。
    - `defi_scheduler` 可在容器内预热聚合缓存。

- [apps/api/app/api/v1/chat.py](/Users/mac-fang/projects/codex/SolonAI/apps/api/app/api/v1/chat.py:1)
  - 每次保存消息时同步刷新 `chat_session.updated_at`。
  - 目的：
    - 会话列表可按最近活动排序。
    - 避免历史会话列表顺序不正确。

- [docker-compose.yml](/Users/mac-fang/projects/codex/SolonAI/docker-compose.yml:1)
  - 更新 `web` 环境变量中的 `NEXT_PUBLIC_API_URL`。
  - `api` 服务补充正确的 `PYTHONPATH`。
  - `api` 服务启动命令改为：
    - 先初始化数据库
    - 再启动 `uvicorn`

### 2.3 Web / 前端相关

- [apps/web/Dockerfile](/Users/mac-fang/projects/codex/SolonAI/apps/web/Dockerfile:1)
  - 切到 `node:20-alpine`
  - 修复 `public/` 目录不存在时构建失败的问题
  - 修复 Next standalone 产物路径与 `server.js` 启动路径不匹配的问题
  - 确保容器内能正确启动 `web` 服务

- [apps/web/src/app/layout.tsx](/Users/mac-fang/projects/codex/SolonAI/apps/web/src/app/layout.tsx:1)
  - 移除在线 Google Fonts 依赖
  - 避免构建受外网字体拉取影响

- [apps/web/src/components/chat/MessageBubble.tsx](/Users/mac-fang/projects/codex/SolonAI/apps/web/src/components/chat/MessageBubble.tsx:1)
  - 去掉对 `react-markdown` / `remark-gfm` 的强依赖使用
  - 目标是让当前依赖状态下编译更稳定

- [apps/web/src/app/strategy/[id]/page.tsx](/Users/mac-fang/projects/codex/SolonAI/apps/web/src/app/strategy/[id]/page.tsx:1)
  - 标记为动态路由渲染，避免之前构建阶段相关报错

- [apps/web/src/lib/api-client.ts](/Users/mac-fang/projects/codex/SolonAI/apps/web/src/lib/api-client.ts:1)
  - 新增：
    - `chatApi.getSessions`
    - `chatApi.getMessages`
  - 为前端恢复聊天会话与历史消息提供 API 封装

- [apps/web/src/app/ai/page.tsx](/Users/mac-fang/projects/codex/SolonAI/apps/web/src/app/ai/page.tsx:1)
  - 增加历史会话恢复逻辑
  - 增加本地 `localStorage` 持久化逻辑
  - 增加 `guest` / 全局最近聊天快照回退逻辑
  - 避免首屏加载时空状态覆盖已保存的历史
  - 说明：
    - 这是今天为“切页后历史丢失”做的多轮修复入口之一
    - 但问题最终仍未确认彻底解决

- [apps/web/src/components/chat/ChatWindow.tsx](/Users/mac-fang/projects/codex/SolonAI/apps/web/src/components/chat/ChatWindow.tsx:1)
  - 将右下角悬浮聊天窗接入会话恢复逻辑
  - 补上钱包地址参与请求
  - 增加本地持久化与最近快照逻辑
  - 避免空状态覆盖本地历史
  - 说明：
    - 这是另一条聊天入口的修复
    - 但问题最终仍未确认彻底解决

### 2.4 Blockchain 相关

- [services/blockchain/providers/marginfi.py](/Users/mac-fang/projects/codex/SolonAI/services/blockchain/providers/marginfi.py:1)
  - 当前文件有用户本地改动，今天联调时已实际验证其集成可工作。
  - 未主动回滚或重置。

- [services/blockchain/tests/**init**.py](/Users/mac-fang/projects/codex/SolonAI/services/blockchain/tests/__init__.py:1)
  - 修复 Devnet 集成测试“假通过”问题
  - 之前的问题：
    - Raydium 报价失败时只打印 warning，但最终仍标记为通过
    - Airdrop 失败时只打印 warning，但最终仍标记为通过
  - 现在行为：
    - 失败会真正 `raise`
    - 汇总后若任何测试失败，脚本以非零退出码结束

### 2.5 新增脚本与配置

- [scripts/docker_smoke_test.sh](/Users/mac-fang/projects/codex/SolonAI/scripts/docker_smoke_test.sh:1)
  - 新增 Docker smoke test 脚本
  - 可一键验证 API / AI / blockchain / web 的基本链路

- [.dockerignore](/Users/mac-fang/projects/codex/SolonAI/.dockerignore:1)
  - 新增 Docker 构建忽略文件
  - 目的：
    - 大幅减少构建上下文
    - 避免把 `.git`、`node_modules`、`.venv`、`.next`、缓存文件带进构建上下文

## 3. 今天完成的联调结果

### 3.1 Docker 服务

成功在 Docker 中拉起以下服务：

- `web`
- `api`
- `db`
- `redis`

验证方式：

```bash
docker compose ps
```

### 3.2 API / AI / Blockchain 联调通过项

已验证通过的接口或链路：

- `GET /health`
  - 返回 `200`
  - Redis 在 Docker 中为 `connected`

- `GET /api/v1/chat/health`
  - 返回 `200`
  - `service=ai-chat`

- `GET /api/v1/assets/{wallet}`
  - 返回真实钱包资产

- `GET /api/v1/defi/overview`
  - 返回 DeFi 聚合数据

- `GET /api/v1/defi/prices`
  - 返回实时价格

- `GET /api/v1/defi/cache/stats`
  - 返回缓存统计

- `GET /api/v1/transactions/history/{wallet}`
  - 返回链上交易历史

- `POST /api/v1/chat/message`
  - 返回 `200`
  - AI 能生成资产总结回复

- `http://web:3000`
  - 容器内可访问首页 HTML

### 3.3 Smoke test 脚本实际跑通

执行成功：

```bash
./scripts/docker_smoke_test.sh
```

脚本会验证：

- Docker 服务是否起来
- API 健康检查
- AI 健康检查
- 资产接口
- DeFi 聚合接口
- 交易历史接口
- AI 对话接口
- 前端首页可达性

## 4. 详细测试步骤

### 4.1 启动 Docker 环境

首次或需要重建镜像时：

```bash
docker compose up -d --build
```

如果只是启动已有镜像：

```bash
docker compose up -d
```

查看状态：

```bash
docker compose ps
```

### 4.2 运行 smoke test

如果服务已经启动：

```bash
./scripts/docker_smoke_test.sh
```

如果想让脚本前先自动拉起服务：

```bash
./scripts/docker_smoke_test.sh --up
```

### 4.3 单独验证 API

容器内执行：

```bash
docker compose exec -T api python - <<'PY'
import urllib.request

for url in [
    'http://127.0.0.1:8000/health',
    'http://127.0.0.1:8000/api/v1/chat/health',
]:
    with urllib.request.urlopen(url, timeout=30) as r:
        print(url, r.status, r.read().decode())
PY
```

### 4.4 单独验证 AI 对话

```bash
docker compose exec -T api python - <<'PY'
import json
import urllib.request

req = urllib.request.Request(
    'http://127.0.0.1:8000/api/v1/chat/message',
    data=json.dumps({
        'message': '帮我概括一下我这个钱包的资产情况',
        'wallet_address': 'vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg',
        'session_id': 'docker-smoke-test'
    }).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST',
)

with urllib.request.urlopen(req, timeout=120) as r:
    print(r.status)
    print(r.read().decode())
PY
```

### 4.5 单独验证 blockchain 集成测试

```bash
apps/api/.venv/bin/python services/blockchain/tests/__init__.py
```

说明：

- 现在这个脚本已经不会“假通过”
- 只要某一项失败，退出码就会是非零

### 4.6 单独验证前端类型

```bash
npm --prefix apps/web run type-check
```

### 4.7 重新验证 API 镜像构建

```bash
docker compose build api
```

说明：

- 本次已确认之前那条 AI 依赖冲突告警已消失

## 5. 今天的实际测试观察

### 5.1 Blockchain 集成测试当前状态

本次运行结果：

- `RPC 客户端`：通过
- `钱包服务`：通过
- `Jupiter`：通过
- `Raydium`：通过
- `交易聚合`：通过
- `Airdrop`：失败

失败原因示例：

- `RPCConnectionError: RPC 连接失败 [https://api.devnet.solana.com]`

这次失败是“真实失败”，脚本已按失败退出，这正是想要的行为。

### 5.2 AI 对话历史问题

今天做过的修复方向：

- `/ai` 页面恢复会话列表与消息历史
- 悬浮聊天窗恢复历史
- 钱包 key / guest key / 全局最近快照 多层回退
- 防止组件刚挂载时空状态覆盖本地历史
- 会话写消息时刷新后端 `updated_at`

但最终状态是：

- 用户反馈“页面切换后，两边的对话都无法保留”
- 该问题未确认解决

因此这个问题应视为：

**未解决，需要前端工程师继续接手。**

## 6. 建议前端继续排查的方向

建议前端工程师优先检查以下几类问题：

1. 是否真实发生了“恢复成功后又被后续 effect 覆盖”
   - 重点关注：
     - `useEffect` 顺序
     - wallet 状态变化
     - route 切换后二次初始化

2. 是否页面入口不一致
   - `/ai` 页面与 `FloatingAIButton -> ChatWindow` 是两套入口
   - 两边当前都加了恢复逻辑，但仍可能存在状态源不一致

3. 是否存在消息写入成功、渲染失败的情况
   - 可直接在浏览器里看：
     - `localStorage['solon-ai:chat:last']`
     - `localStorage['solon-ai:chat:guest']`
     - `localStorage['solon-ai:chat:<walletAddress>']`

4. 是否后端 session / messages 已落库但前端没有拉取出来
   - 可直接查数据库：

```bash
docker compose exec -T db psql -U solon -d solon_ai -c "select session_id, title, updated_at from chat_sessions order by updated_at desc limit 10;"
docker compose exec -T db psql -U solon -d solon_ai -c "select role, content, created_at from chat_messages order by created_at desc limit 20;"
```

5. 是否某处仍然使用旧的纯内存 state 逻辑
   - 特别关注：
     - 路由切换
     - 组件卸载重挂载
     - 是否有别处重新初始化 `messages=[]`

## 7. 当前建议的交接结论

### 已可交付部分

- Docker 联调链路可用
- smoke test 已沉淀
- AI / blockchain / 前后端主要链路已验证
- blockchain 集成测试“假通过”已修复
- API 构建依赖告警已消除

### 待前端继续处理部分

- 页面切换后聊天历史丢失
- 需要前端工程师结合浏览器 DevTools、组件挂载顺序与实际交互路径继续定位

## 8. 推荐的最小交接话术

可直接给前端工程师：

> Docker 联调、AI / blockchain 接口、smoke test 和假通过问题已经处理完成。当前未解决的问题只剩“页面切换后聊天历史丢失”。我已经在 `/ai` 页面和悬浮聊天窗两套入口都加过恢复逻辑、本地存储兜底和最近聊天快照，但用户实测仍反馈无效。建议你从 `apps/web/src/app/ai/page.tsx`、`apps/web/src/components/chat/ChatWindow.tsx`、`apps/web/src/lib/api-client.ts` 和浏览器 localStorage / route 切换生命周期继续往下查。
