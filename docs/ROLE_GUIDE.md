# 开发者角色指南

> 根据你的角色，快速了解你需要做什么

## 🎨 前端开发者指南

### 你的工作目录
```
apps/web/
├── src/
│   ├── app/              # 你要创建的页面
│   ├── components/       # 你要开发的组件
│   ├── lib/             # 你要使用的工具
│   └── services/        # 你要调用的API
```

### 第一周任务清单

#### Day 1-2: 钱包连接功能
- [ ] 完善 `WalletProvider.tsx` 的钱包连接逻辑
- [ ] 创建 `WalletButton.tsx` 组件（连接/断开按钮）
- [ ] 创建 `WalletInfo.tsx` 组件（显示地址和余额）
- [ ] 测试 Phantom 和 Solflare 钱包

**参考代码位置**: `apps/web/src/components/wallet/`

**你需要实现的功能**:
```typescript
// WalletButton.tsx
export function WalletButton() {
  const { connected, connect, disconnect, publicKey } = useWallet();

  // TODO: 实现连接按钮UI
  // TODO: 实现断开连接逻辑
  // TODO: 显示钱包地址（缩短格式）
  // TODO: 添加复制地址功能
}
```

#### Day 3-4: 资产展示页面
- [ ] 创建 `app/dashboard/page.tsx` 资产总览页面
- [ ] 创建 `AssetCard.tsx` 组件（单个资产卡片）
- [ ] 创建 `AssetList.tsx` 组件（资产列表）
- [ ] 调用后端API获取资产数据
- [ ] 实现加载状态和错误处理

**你需要创建的文件**:
```
apps/web/src/
├── app/dashboard/
│   └── page.tsx          # 创建这个
├── components/assets/
│   ├── AssetCard.tsx     # 创建这个
│   └── AssetList.tsx     # 创建这个
└── services/
    └── assets.ts         # 创建这个
```

**API调用示例**:
```typescript
// services/assets.ts
export async function getAssets(walletAddress: string) {
  const response = await apiClient.get(`/assets/balance?address=${walletAddress}`);
  return response.data;
}

// app/dashboard/page.tsx
export default function DashboardPage() {
  const { publicKey } = useWallet();
  const { data, isLoading } = useQuery(
    ['assets', publicKey?.toString()],
    () => getAssets(publicKey!.toString())
  );

  // TODO: 渲染资产列表
  // TODO: 显示总资产价值
  // TODO: 显示资产分布饼图
}
```

#### Day 5-7: 策略配置表单
- [ ] 创建 `app/strategy/page.tsx` 策略页面
- [ ] 创建 `StrategyForm.tsx` 组件（策略配置表单）
- [ ] 创建 `StrategyCard.tsx` 组件（策略展示卡片）
- [ ] 实现表单验证
- [ ] 调用后端API生成策略

**表单字段**:
- 投资金额
- 代币选择
- 风险偏好（保守/平衡/激进）
- 投资期限

### 第二周任务清单

#### Day 8-10: 聊天界面
- [ ] 创建 `ChatWindow.tsx` 组件
- [ ] 创建 `MessageList.tsx` 组件
- [ ] 创建 `MessageInput.tsx` 组件
- [ ] 实现消息发送和接收
- [ ] 集成AI对话API

#### Day 11-12: 交易确认流程
- [ ] 创建 `TransactionModal.tsx` 组件
- [ ] 显示交易详情（金额、Gas费、预期收益）
- [ ] 实现钱包签名流程
- [ ] 显示交易状态（pending/success/failed）

#### Day 13-14: 优化和测试
- [ ] 添加加载动画
- [ ] 优化移动端适配
- [ ] 错误边界处理
- [ ] 端到端测试

### 关键技术点

#### 1. 如何连接钱包
```typescript
import { useWallet } from '@solana/wallet-adapter-react';

function MyComponent() {
  const { connected, publicKey, signTransaction } = useWallet();

  if (!connected) {
    return <div>请先连接钱包</div>;
  }

  return <div>已连接: {publicKey?.toString()}</div>;
}
```

#### 2. 如何调用API
```typescript
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';

// 查询数据
const { data, isLoading } = useQuery(['key'], async () => {
  const res = await apiClient.get('/endpoint');
  return res.data;
});

// 提交数据
const mutation = useMutation(async (data) => {
  const res = await apiClient.post('/endpoint', data);
  return res.data;
});
```

#### 3. 如何签名交易
```typescript
import { Transaction } from '@solana/web3.js';

async function signAndSendTransaction(transaction: Transaction) {
  const { signTransaction, sendTransaction } = useWallet();

  // 签名
  const signed = await signTransaction(transaction);

  // 发送
  const signature = await sendTransaction(signed, connection);

  // 等待确认
  await connection.confirmTransaction(signature);
}
```

---

## ⚙️ 后端开发者指南

### 你的工作目录
```
apps/api/
├── app/
│   ├── api/v1/          # 你要实现的API路由
│   ├── services/        # 你要编写的业务逻辑
│   ├── models/          # 你要定义的数据模型
│   └── schemas/         # 你要定义的请求/响应模型
```

### 第一周任务清单

#### Day 1-2: 认证系统
- [ ] 完善 `app/api/v1/auth.py` 的认证接口
- [ ] 实现用户注册逻辑
- [ ] 实现用户登录逻辑
- [ ] 实现JWT Token生成和验证
- [ ] 创建用户数据模型

**你需要实现的接口**:
```python
# app/api/v1/auth.py

@router.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    用户注册
    TODO:
    1. 验证钱包地址格式
    2. 检查用户是否已存在
    3. 创建用户记录
    4. 生成JWT Token
    5. 返回用户信息和Token
    """
    pass

@router.post("/login")
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录
    TODO:
    1. 验证钱包签名
    2. 查询用户信息
    3. 生成JWT Token
    4. 返回Token
    """
    pass
```

#### Day 3-4: 资产查询接口
- [ ] 完善 `app/api/v1/assets.py` 的资产接口
- [ ] 实现余额查询逻辑
- [ ] 实现代币列表查询
- [ ] 实现历史记录查询
- [ ] 添加Redis缓存

**你需要实现的接口**:
```python
# app/api/v1/assets.py

@router.get("/balance")
async def get_balance(
    address: str,
    current_user: User = Depends(get_current_user),
    redis: Redis = Depends(get_redis)
):
    """
    查询用户资产余额
    TODO:
    1. 验证地址格式
    2. 检查Redis缓存
    3. 如果没有缓存,调用Blockchain Service
    4. 查询SOL余额
    5. 查询所有SPL Token余额
    6. 计算总价值(USD)
    7. 缓存结果(TTL: 60s)
    8. 返回资产列表
    """
    pass

@router.get("/tokens")
async def get_tokens(
    address: str,
    current_user: User = Depends(get_current_user)
):
    """
    查询用户持有的代币列表
    TODO:
    1. 调用Solana RPC获取Token Accounts
    2. 获取每个代币的元数据
    3. 获取代币价格
    4. 返回代币列表
    """
    pass
```

#### Day 5-7: 策略生成接口
- [ ] 完善 `app/api/v1/strategy.py` 的策略接口
- [ ] 实现策略生成逻辑
- [ ] 对接AI服务
- [ ] 保存策略到数据库
- [ ] 实现策略查询

**你需要实现的接口**:
```python
# app/api/v1/strategy.py

@router.post("/generate")
async def generate_strategy(
    request: StrategyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成投资策略
    TODO:
    1. 验证请求参数
    2. 查询用户资产
    3. 调用AI Agents Service
    4. 等待AI生成策略
    5. 保存策略到数据库
    6. 返回策略方案
    """
    # 调用AI服务
    ai_response = await call_ai_service({
        "user_input": request.message,
        "user_assets": user_assets,
        "risk_level": request.risk_level
    })

    # 保存策略
    strategy = Strategy(
        user_id=current_user.id,
        type=ai_response["strategy_type"],
        details=ai_response["details"]
    )
    db.add(strategy)
    db.commit()

    return strategy
```

### 第二周任务清单

#### Day 8-10: 交易执行接口
- [ ] 实现交易构建接口
- [ ] 实现交易提交接口
- [ ] 实现交易状态查询
- [ ] 添加交易监听

#### Day 11-12: 数据库优化
- [ ] 创建数据库迁移脚本
- [ ] 添加索引优化查询
- [ ] 实现数据库连接池
- [ ] 添加数据备份

#### Day 13-14: 测试和文档
- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] 完善API文档
- [ ] 性能测试

### 关键技术点

#### 1. 如何调用AI服务
```python
import httpx

async def call_ai_service(data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://ai-agents:8001/generate",
            json=data,
            timeout=30.0
        )
        return response.json()
```

#### 2. 如何使用Redis缓存
```python
from redis import Redis

async def get_with_cache(key: str, fetch_func, ttl: int = 60):
    # 尝试从缓存获取
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)

    # 缓存未命中,调用函数获取
    data = await fetch_func()

    # 存入缓存
    await redis.setex(key, ttl, json.dumps(data))

    return data
```

#### 3. 如何调用区块链服务
```python
from services.blockchain.solana.rpc_client import SolanaRPCClient

client = SolanaRPCClient(settings.SOLANA_RPC_URL)

# 查询余额
balance = await client.get_balance(address)

# 查询代币
tokens = await client.get_token_accounts(address)
```

---

## 🤖 AI开发者指南

### 你的工作目录
```
services/ai-agents/
├── agents/              # 你要完善的Agent
├── graphs/              # 你要优化的工作流
├── prompts/             # 你要编写的Prompt
├── tools/               # 你要创建的工具
└── rag/                 # 你要构建的知识库
```

### 第一周任务清单

#### Day 1-2: Intent Agent (意图识别)
- [ ] 完善 `agents/intent_agent.py` 的TODO部分
- [ ] 编写意图识别Prompt
- [ ] 实现实体提取逻辑
- [ ] 测试各种用户输入

**你需要实现的功能**:
```python
# agents/intent_agent.py

async def intent_agent(state: AgentState) -> AgentState:
    """
    意图识别Agent
    TODO:
    1. 获取用户输入
    2. 调用LLM分析意图
    3. 提取关键实体(金额、代币、风险偏好等)
    4. 分类意图类型(lending/swap/stake等)
    5. 返回结构化结果
    """
    user_input = state["user_input"]

    # 构建Prompt
    prompt = f"""
    分析用户意图并提取关键信息:

    用户输入: {user_input}

    请识别:
    1. 意图类型 (lending/swap/stake/query)
    2. 金额和代币
    3. 风险偏好
    4. 时间期限

    以JSON格式返回。
    """

    # 调用LLM
    response = await llm.ainvoke(prompt)

    # 解析结果
    intent = parse_intent(response)

    state["intent"] = intent
    return state
```

**测试用例**:
- "我想用1000 USDC赚取稳定收益" → lending, conservative
- "帮我把SOL换成USDC" → swap
- "查询我的资产" → query

#### Day 3-4: Strategy Agent (策略生成)
- [ ] 完善 `agents/strategy_agent.py` 的TODO部分
- [ ] 构建RAG知识库（DeFi协议信息）
- [ ] 实现策略生成逻辑
- [ ] 计算预期收益

**你需要实现的功能**:
```python
# agents/strategy_agent.py

async def strategy_agent(state: AgentState) -> AgentState:
    """
    策略生成Agent
    TODO:
    1. 获取意图分析结果
    2. 查询RAG知识库获取协议信息
    3. 调用LLM生成策略
    4. 计算预期收益和风险
    5. 生成执行步骤
    """
    intent = state["intent"]

    # 查询知识库
    protocols = await rag.search(
        query=f"{intent['type']} protocols on Solana",
        top_k=3
    )

    # 构建Prompt
    prompt = f"""
    根据用户意图生成DeFi策略:

    意图: {intent}
    可用协议: {protocols}

    请生成:
    1. 推荐协议和理由
    2. 具体操作步骤
    3. 预期收益率
    4. 风险提示
    """

    # 调用LLM
    response = await llm.ainvoke(prompt)

    state["strategy"] = parse_strategy(response)
    return state
```

#### Day 5-7: Risk Agent (风险评估)
- [ ] 完善 `agents/risk_agent.py` 的TODO部分
- [ ] 实现代币风险检测
- [ ] 实现协议风险检测
- [ ] 实现用户风险检测

**风险检测项**:
- 代币合约是否安全
- 协议TVL是否充足
- 是否有审计报告
- 用户资产配置是否合理

### 第二周任务清单

#### Day 8-10: RAG知识库
- [ ] 收集DeFi协议文档
- [ ] 构建向量数据库
- [ ] 实现文档检索
- [ ] 优化检索效果

#### Day 11-12: 工作流优化
- [ ] 优化Agent之间的协同
- [ ] 添加错误重试机制
- [ ] 实现流式输出
- [ ] 添加日志记录

#### Day 13-14: 测试和优化
- [ ] 端到端测试
- [ ] Prompt优化
- [ ] 性能优化
- [ ] 成本优化

### 关键技术点

#### 1. 如何使用LangGraph
```python
from langgraph.graph import StateGraph, END

def create_workflow():
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("intent", intent_agent)
    workflow.add_node("strategy", strategy_agent)
    workflow.add_node("risk", risk_agent)

    # 添加边
    workflow.add_edge("intent", "strategy")
    workflow.add_edge("strategy", "risk")
    workflow.add_edge("risk", END)

    # 设置入口
    workflow.set_entry_point("intent")

    return workflow.compile()
```

#### 2. 如何调用LLM
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4", temperature=0)

response = await llm.ainvoke([
    {"role": "system", "content": "你是DeFi专家"},
    {"role": "user", "content": "用户问题"}
])
```

#### 3. 如何使用RAG
```python
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings

# 初始化
vectorstore = PineconeVectorStore(
    index_name="defi-knowledge",
    embedding=OpenAIEmbeddings()
)

# 检索
docs = await vectorstore.asimilarity_search(
    query="MarginFi lending",
    k=3
)
```

---

## ⛓️ 区块链开发者指南

### 你的工作目录
```
services/blockchain/
├── solana/              # Solana基础功能
├── defi/                # DeFi协议集成
└── utils/               # 工具函数
```

### 第一周任务清单

#### Day 1-2: Solana RPC客户端
- [ ] 完善 `solana/rpc_client.py` 的TODO部分
- [ ] 实现余额查询
- [ ] 实现代币账户查询
- [ ] 实现交易历史查询

**你需要实现的功能**:
```python
# solana/rpc_client.py

class SolanaRPCClient:
    async def get_balance(self, address: str) -> float:
        """
        查询SOL余额
        TODO:
        1. 验证地址格式
        2. 调用RPC getBalance
        3. 转换lamports到SOL
        4. 返回余额
        """
        pass

    async def get_token_accounts(self, address: str) -> List[TokenAccount]:
        """
        查询所有SPL Token账户
        TODO:
        1. 调用RPC getTokenAccountsByOwner
        2. 解析账户数据
        3. 获取代币元数据
        4. 返回代币列表
        """
        pass
```

#### Day 3-4: Jupiter集成
- [ ] 完善 `defi/jupiter.py` 的TODO部分
- [ ] 实现价格查询
- [ ] 实现路由查询
- [ ] 实现交易构建

**你需要实现的功能**:
```python
# defi/jupiter.py

class JupiterClient:
    async def get_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int
    ) -> Quote:
        """
        获取交易报价
        TODO:
        1. 调用Jupiter API获取报价
        2. 解析路由信息
        3. 计算价格影响
        4. 返回最优报价
        """
        pass

    async def build_swap_transaction(
        self,
        quote: Quote,
        user_public_key: str
    ) -> Transaction:
        """
        构建交换交易
        TODO:
        1. 调用Jupiter API获取交易
        2. 反序列化交易
        3. 添加优先费用
        4. 返回未签名交易
        """
        pass
```

#### Day 5-7: MarginFi集成
- [ ] 完善 `defi/marginfi.py` 的TODO部分
- [ ] 实现存款功能
- [ ] 实现取款功能
- [ ] 实现借款功能

### 第二周任务清单

#### Day 8-10: 更多协议集成
- [ ] 集成Kamino (借贷)
- [ ] 集成Drift (永续合约)
- [ ] 集成Raydium (AMM)

#### Day 11-12: 交易工具
- [ ] 实现交易模拟
- [ ] 实现Gas估算
- [ ] 实现交易监听
- [ ] 实现错误处理

#### Day 13-14: 测试和优化
- [ ] 在Devnet测试
- [ ] 优化RPC调用
- [ ] 添加重试机制
- [ ] 性能测试

### 关键技术点

#### 1. 如何调用Solana RPC
```python
from solana.rpc.async_api import AsyncClient

client = AsyncClient("https://api.mainnet-beta.solana.com")

# 查询余额
response = await client.get_balance(pubkey)
balance = response.value / 1e9  # lamports to SOL

# 查询代币账户
response = await client.get_token_accounts_by_owner(
    pubkey,
    {"programId": TOKEN_PROGRAM_ID}
)
```

#### 2. 如何构建交易
```python
from solana.transaction import Transaction
from solana.system_program import transfer, TransferParams

# 创建转账指令
instruction = transfer(
    TransferParams(
        from_pubkey=sender,
        to_pubkey=receiver,
        lamports=amount
    )
)

# 构建交易
transaction = Transaction()
transaction.add(instruction)
```

#### 3. 如何调用Jupiter API
```python
import httpx

async def get_jupiter_quote(input_mint, output_mint, amount):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://quote-api.jup.ag/v6/quote",
            params={
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": amount,
                "slippageBps": 50
            }
        )
        return response.json()
```

---

## 📞 需要帮助?

- **技术问题**: 在团队群里提问
- **代码审查**: 提交PR后@相关负责人
- **架构疑问**: 查看 `docs/ARCHITECTURE.md`
- **紧急问题**: 联系项目负责人

记住: **先看文档,再问问题,多写注释,勤提交代码!** 🚀
