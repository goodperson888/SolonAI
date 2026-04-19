# 快速开始指南

## 新成员入职指南

欢迎加入 Solon AI 团队！本指南将帮助你快速上手项目开发。

### 第一天：环境搭建

#### 1. 安装必要工具

**必装工具**
- [Node.js 18+](https://nodejs.org/)
- [Python 3.11+](https://www.python.org/)
- [Git](https://git-scm.com/)
- [VS Code](https://code.visualstudio.com/) (推荐)

**可选工具**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Postman](https://www.postman.com/) (API测试)

#### 2. 克隆项目

```bash
git clone https://github.com/your-org/solon-ai.git
cd solon-ai
```

#### 3. 安装依赖

```bash
# 根目录安装前端依赖
npm install

# 后端依赖
cd apps/api
pip install -r requirements.txt
cd ../..

# AI服务依赖
cd services/ai-agents
pip install -r requirements.txt
cd ../..

# 区块链服务依赖
cd services/blockchain
pip install -r requirements.txt
cd ../..
```

#### 4. 配置环境变量

复制环境变量模板并填写：

```bash
cp apps/web/.env.example apps/web/.env.local
cp apps/api/.env.example apps/api/.env
cp services/ai-agents/.env.example services/ai-agents/.env
```

**获取必要的API Key**
- Alchemy Solana RPC: https://www.alchemy.com/
- 豆包/通义千问: https://www.volcengine.com/product/doubao

#### 5. 启动开发环境

**方式1: Docker Compose (推荐)**
```bash
docker-compose up -d
```

**方式2: 手动启动**
```bash
# 终端1: 前端
cd apps/web && npm run dev

# 终端2: 后端
cd apps/api && source .venv/bin/activate && python -m uvicorn main:app --reload

# 终端3: 数据库 (如果没用Docker)
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15
```

#### 5.1 推荐日常模式：SQLite

默认推荐先用 SQLite 做本地联调，不依赖额外数据库服务。

```bash
cp apps/api/.env.sqlite.example apps/api/.env
cd apps/api
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m app.core.init_db
python -m uvicorn main:app --reload --port 8000
```

也可以在项目根目录直接启动整套前后端：

```bash
SOLON_DB_MODE=sqlite ./start.sh
```

#### 5.2 切换开发模式：Postgres

当本地联调稳定后，再切到 Postgres 做开发。项目已经在 `docker-compose.yml` 中提供了本地数据库：

```bash
cp apps/api/.env.postgres.example apps/api/.env
docker compose up -d db
cd apps/api
source .venv/bin/activate
python -m app.core.init_postgres
python -m uvicorn main:app --reload --port 8000
```

或者使用一键启动脚本：

```bash
docker compose up -d db
SOLON_DB_MODE=postgres ./start.sh
```

#### 6. 验证环境

- 访问 http://localhost:3000 (前端)
- 访问 http://localhost:8000/docs (后端API文档)
- 看到欢迎页面即表示成功

### 第二天：熟悉代码

#### 1. 阅读文档

- [需求文档](./需求.md) - 了解产品需求
- [团队协作规范](./团队协作与项目管理规范.md) - 了解开发规范
- [README.md](./README.md) - 项目总览

#### 2. 了解项目结构

```
solon-ai/
├── apps/web/              # 你的前端代码在这里
├── apps/api/              # 你的后端代码在这里
├── services/ai-agents/    # AI智能体代码
├── services/blockchain/   # 区块链交互代码
└── packages/              # 共享代码
```

#### 3. 运行示例

**前端示例**
```bash
cd apps/web
# 查看示例组件
cat src/components/wallet/WalletProvider.tsx
```

**后端示例**
```bash
cd apps/api
# 测试API
curl http://localhost:8000/health
```

### 第三天：开始开发

#### 1. 创建功能分支

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

#### 2. 开发你的功能

根据你的角色选择对应的模块：

**前端开发者**
- 在 `apps/web/src/components/` 创建组件
- 在 `apps/web/src/app/` 创建页面
- 参考现有代码风格

**后端开发者**
- 在 `apps/api/app/api/v1/` 创建API路由
- 在 `apps/api/app/services/` 创建业务逻辑
- 参考现有代码风格

**AI开发者**
- 在 `services/ai-agents/agents/` 创建Agent
- 完善现有Agent的TODO部分
- 测试Agent功能

**区块链开发者**
- 在 `services/blockchain/defi/` 添加协议集成
- 完善现有协议的TODO部分
- 测试链上交互

#### 3. 提交代码

```bash
git add .
git commit -m "feat(module): 添加XXX功能"
git push origin feature/your-feature-name
```

#### 4. 创建Pull Request

1. 访问 GitHub 仓库
2. 点击 "New Pull Request"
3. 选择 `develop` 作为目标分支
4. 填写PR描述
5. 等待代码审查

## 常用命令速查

### 前端开发

```bash
cd apps/web
npm run dev          # 启动开发服务器
npm run build        # 构建生产版本
npm run lint         # 代码检查
npm run test         # 运行测试
```

### 后端开发

```bash
cd apps/api
source .venv/bin/activate
python -m uvicorn main:app --reload
pytest
black .
mypy .
```

### Git操作

```bash
git status                   # 查看状态
git add .                    # 添加所有更改
git commit -m "message"      # 提交
git push                     # 推送
git pull                     # 拉取
git checkout -b feature/xxx  # 创建新分支
```

### Docker操作

```bash
docker-compose up -d         # 启动所有服务
docker-compose down          # 停止所有服务
docker-compose logs -f       # 查看日志
docker-compose ps            # 查看运行状态
```

## 开发技巧

### 1. 使用VS Code插件

推荐安装：
- ESLint
- Prettier
- Python
- Tailwind CSS IntelliSense
- GitLens

### 2. 调试技巧

**前端调试**
- 使用浏览器开发者工具
- 使用 `console.log()` 或 `debugger`
- 使用 React DevTools

**后端调试**
- 使用 `print()` 或 `logging`
- 使用 VS Code 调试器
- 查看 FastAPI 自动生成的文档

### 3. 常见问题

**问题1: 端口被占用**
```bash
# 查找占用端口的进程
lsof -i :3000
# 杀死进程
kill -9 <PID>
```

**问题2: 依赖安装失败**
```bash
# 清除缓存重新安装
npm cache clean --force
npm install
```

**问题3: Docker启动失败**
```bash
# 查看日志
docker-compose logs
# 重新构建
docker-compose build --no-cache
```

## 获取帮助

- **技术问题**: 在团队群里提问
- **Bug报告**: 创建 GitHub Issue
- **代码审查**: 在PR中评论
- **紧急问题**: 联系项目负责人

## 下一步

- 加入每日站会 (每天10:00)
- 认领你的第一个任务
- 开始编码！

祝你开发愉快！🚀
