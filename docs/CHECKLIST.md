# 项目启动检查清单

## 📋 项目负责人检查清单

### 1. GitHub仓库设置
- [ ] 创建GitHub仓库
- [ ] 推送代码到main分支
- [ ] 创建develop分支
- [ ] 设置分支保护规则
  - [ ] main分支：禁止直接推送，需要PR
  - [ ] develop分支：禁止直接推送，需要PR
  - [ ] 要求至少1人审查
- [ ] 添加团队成员到仓库
- [ ] 设置团队权限（Admin/Write/Read）

### 2. 免费服务注册
- [ ] 注册Vercel账号（前端部署）
- [ ] 注册Railway账号（后端部署）
- [ ] 注册Supabase账号（数据库）
- [ ] 注册Upstash账号（Redis）
- [ ] 注册Alchemy账号（Solana RPC）
- [ ] 注册豆包/通义千问账号（大模型）
- [ ] 注册Pinecone账号（向量数据库）
- [ ] 注册Sentry账号（错误监控）

### 3. GitHub Secrets配置
- [ ] 添加 `VERCEL_TOKEN`
- [ ] 添加 `VERCEL_ORG_ID`
- [ ] 添加 `VERCEL_PROJECT_ID`
- [ ] 添加 `RAILWAY_TOKEN`

### 4. 团队沟通
- [ ] 创建团队群（微信/钉钉/飞书）
- [ ] 分享项目仓库链接
- [ ] 分享文档链接
- [ ] 安排第一次团队会议
- [ ] 分配任务和角色

### 5. 文档准备
- [ ] 确认所有文档已创建
- [ ] 确认架构图清晰
- [ ] 确认开发指南完整
- [ ] 准备新人培训材料

---

## 👥 团队成员检查清单

### 第一天：环境搭建

#### 1. 安装开发工具
- [ ] 安装Node.js 18+ (https://nodejs.org/)
- [ ] 安装Python 3.11+ (https://www.python.org/)
- [ ] 安装Git (https://git-scm.com/)
- [ ] 安装VS Code (https://code.visualstudio.com/)
- [ ] 安装Docker Desktop (可选，https://www.docker.com/)

#### 2. 克隆项目
```bash
# 克隆仓库
git clone https://github.com/your-org/solon-ai.git
cd solon-ai

# 查看分支
git branch -a

# 切换到develop分支
git checkout develop
```

#### 3. 安装依赖

**前端和共享包**
```bash
# 在项目根目录
npm install
```

**后端**
```bash
cd apps/api
pip install -r requirements.txt
cd ../..
```

**AI服务**
```bash
cd services/ai-agents
pip install -r requirements.txt
cd ../..
```

**区块链服务**
```bash
cd services/blockchain
pip install -r requirements.txt
cd ../..
```

#### 4. 配置环境变量

**前端**
```bash
cp apps/web/.env.example apps/web/.env.local
# 编辑 apps/web/.env.local，填入配置
```

**后端**
```bash
cp apps/api/.env.example apps/api/.env
# 编辑 apps/api/.env，填入配置
```

**AI服务**
```bash
cp services/ai-agents/.env.example services/ai-agents/.env
# 编辑 services/ai-agents/.env，填入配置
```

#### 5. 测试环境

**前端**
```bash
cd apps/web
npm run dev
# 访问 http://localhost:3000
```

**后端**
```bash
cd apps/api
uvicorn main:app --reload
# 访问 http://localhost:8000/docs
```

#### 6. 创建你的第一个分支
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-name-first-task
```

---

## 🎨 前端开发者检查清单

### 开发前准备
- [ ] 阅读 `docs/ROLE_GUIDE.md` 前端部分
- [ ] 阅读 `docs/ARCHITECTURE.md` 前端架构
- [ ] 熟悉 Next.js 14 App Router
- [ ] 熟悉 Tailwind CSS
- [ ] 了解 Solana Wallet Adapter

### VS Code插件
- [ ] ESLint
- [ ] Prettier
- [ ] Tailwind CSS IntelliSense
- [ ] ES7+ React/Redux/React-Native snippets

### 第一个任务
- [ ] 认领任务（在GitHub Issues或项目看板）
- [ ] 创建功能分支
- [ ] 开始开发
- [ ] 提交PR

---

## ⚙️ 后端开发者检查清单

### 开发前准备
- [ ] 阅读 `docs/ROLE_GUIDE.md` 后端部分
- [ ] 阅读 `docs/ARCHITECTURE.md` 后端架构
- [ ] 熟悉 FastAPI
- [ ] 了解 PostgreSQL 和 Redis
- [ ] 了解 JWT 认证

### VS Code插件
- [ ] Python
- [ ] Pylance
- [ ] Python Docstring Generator
- [ ] SQLTools

### 数据库设置
- [ ] 启动本地PostgreSQL（Docker或本地安装）
- [ ] 创建数据库 `solon_ai`
- [ ] 运行迁移脚本（如果有）

### 第一个任务
- [ ] 认领任务
- [ ] 创建功能分支
- [ ] 开始开发
- [ ] 编写测试
- [ ] 提交PR

---

## 🤖 AI开发者检查清单

### 开发前准备
- [ ] 阅读 `docs/ROLE_GUIDE.md` AI部分
- [ ] 阅读 `docs/ARCHITECTURE.md` AI架构
- [ ] 熟悉 LangChain 和 LangGraph
- [ ] 了解 RAG 原理
- [ ] 获取 OpenAI/豆包 API Key

### Python环境
- [ ] 创建虚拟环境
```bash
cd services/ai-agents
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 测试LLM连接
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(api_key="your-key")
response = llm.invoke("Hello!")
print(response)
```

### 第一个任务
- [ ] 认领任务
- [ ] 创建功能分支
- [ ] 开始开发Agent
- [ ] 测试Agent功能
- [ ] 提交PR

---

## ⛓️ 区块链开发者检查清单

### 开发前准备
- [ ] 阅读 `docs/ROLE_GUIDE.md` 区块链部分
- [ ] 阅读 `docs/ARCHITECTURE.md` 区块链架构
- [ ] 熟悉 Solana Web3.py
- [ ] 了解 Jupiter、MarginFi 等协议
- [ ] 获取 Alchemy API Key

### 钱包设置
- [ ] 安装 Phantom 钱包
- [ ] 切换到 Devnet
- [ ] 获取测试SOL（https://faucet.solana.com/）

### 测试RPC连接
```python
from solana.rpc.async_api import AsyncClient

client = AsyncClient("https://api.devnet.solana.com")
response = await client.is_connected()
print(response)
```

### 第一个任务
- [ ] 认领任务
- [ ] 创建功能分支
- [ ] 在Devnet测试
- [ ] 提交PR

---

## 📝 每日工作流程

### 早上（开始工作前）
1. [ ] 参加每日站会（10:00）
2. [ ] 拉取最新代码
```bash
git checkout develop
git pull origin develop
git checkout your-branch
git merge develop
```
3. [ ] 查看今天的任务
4. [ ] 开始编码

### 晚上（结束工作前）
1. [ ] 提交代码
```bash
git add .
git commit -m "feat(module): 完成XXX功能"
git push origin your-branch
```
2. [ ] 如果功能完成，创建PR
3. [ ] 更新任务状态
4. [ ] 记录明天的计划

---

## 🚨 常见问题解决

### 问题1: 端口被占用
```bash
# 查找占用端口的进程
lsof -i :3000
# 杀死进程
kill -9 <PID>
```

### 问题2: 依赖安装失败
```bash
# 清除缓存
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### 问题3: Git冲突
```bash
# 拉取最新代码
git pull origin develop
# 解决冲突
# 提交
git add .
git commit -m "fix: 解决合并冲突"
```

### 问题4: Docker启动失败
```bash
# 查看日志
docker-compose logs
# 重新构建
docker-compose build --no-cache
docker-compose up -d
```

---

## 📞 获取帮助

### 技术问题
1. 先查看文档
   - README.md
   - docs/GETTING_STARTED.md
   - docs/ARCHITECTURE.md
   - docs/ROLE_GUIDE.md

2. 搜索GitHub Issues

3. 在团队群提问

4. 联系对应的Leader

### 紧急问题
- 联系项目负责人
- 电话: [填写]
- 微信: [填写]

---

## ✅ 准备就绪检查

在开始开发前，确认以下所有项都已完成：

- [ ] 已克隆项目代码
- [ ] 已安装所有依赖
- [ ] 已配置环境变量
- [ ] 能成功启动开发服务器
- [ ] 已阅读相关文档
- [ ] 已加入团队群
- [ ] 已认领第一个任务
- [ ] 已创建功能分支

**如果以上全部完成，恭喜你！可以开始编码了！🎉**

---

## 📅 2周冲刺计划

### Week 1: 核心功能开发
- Day 1-2: 环境搭建 + 基础功能
- Day 3-5: 核心业务逻辑
- Day 6-7: 联调测试

### Week 2: 完善和上线
- Day 8-11: 功能完善 + Bug修复
- Day 12-13: 集成测试 + 优化
- Day 14: 部署上线 + 庆祝🎉

**目标**: 2周后发布可用的MVP版本！

加油！💪
