# Blockchain Service

区块链交互服务，提供Solana链上操作和DeFi协议集成。

## 目录结构

```
blockchain/
├── solana/              # Solana基础交互
│   ├── rpc_client.py   # RPC客户端封装
│   └── __init__.py
├── defi/               # DeFi协议集成
│   ├── jupiter.py      # Jupiter聚合交易
│   ├── marginfi.py     # MarginFi借贷
│   └── __init__.py
├── utils/              # 工具模块
│   ├── transaction_builder.py  # 交易构建
│   └── __init__.py
├── requirements.txt    # Python依赖
└── README.md
```

## 功能模块

### 1. Solana RPC客户端 (`solana/rpc_client.py`)

提供与Solana区块链的基础交互：

- `get_balance()`: 获取SOL余额
- `get_token_accounts()`: 获取代币账户
- `get_transaction()`: 查询交易详情
- `send_transaction()`: 发送已签名交易

**使用示例：**

```python
from blockchain.solana import SolanaRPCClient

client = SolanaRPCClient()
balance = await client.get_balance("用户钱包地址")
tokens = await client.get_token_accounts("用户钱包地址")
```

### 2. Jupiter聚合交易 (`defi/jupiter.py`)

集成Jupiter协议，提供最优路由的代币兑换：

- `get_quote()`: 获取兑换报价
- `get_swap_transaction()`: 获取兑换交易数据
- `get_token_list()`: 获取支持的代币列表

**使用示例：**

```python
from blockchain.defi import JupiterClient

jupiter = JupiterClient()
quote = await jupiter.get_quote(
    input_mint="SOL地址",
    output_mint="USDC地址",
    amount=1000000000,  # 1 SOL
    slippage_bps=50     # 0.5%滑点
)
```

### 3. MarginFi借贷 (`defi/marginfi.py`)

集成MarginFi协议，提供借贷功能：

- `get_user_account()`: 获取用户账户信息
- `get_lending_pools()`: 获取借贷池列表
- `build_deposit_instruction()`: 构建存款指令
- `build_borrow_instruction()`: 构建借款指令

**注意：** MarginFi模块当前为框架代码，需要根据协议SDK完善实现。

### 4. 交易构建工具 (`utils/transaction_builder.py`)

提供交易构建和序列化功能：

- `build_transaction()`: 构建交易
- `create_instruction()`: 创建指令
- `serialize_transaction()`: 序列化交易

## 环境变量

在 `.env` 文件中配置：

```bash
# Solana RPC节点（免费方案使用Alchemy）
SOLANA_RPC_URL=https://solana-mainnet.g.alchemy.com/v2/YOUR_API_KEY
```

## 安装依赖

```bash
cd services/blockchain
pip install -r requirements.txt
```

## 开发规范

1. **非托管原则**：所有交易必须返回未签名数据，由前端钱包签名
2. **错误处理**：所有外部调用必须捕获异常并返回友好错误信息
3. **类型注解**：使用Python类型提示，提高代码可读性
4. **异步优先**：所有网络请求使用async/await

## 待完善功能

- [ ] MarginFi协议完整实现（需要SDK或手动解析账户数据）
- [ ] 添加更多DeFi协议（Kamino、Drift等）
- [ ] 交易模拟和Gas估算
- [ ] 代币价格查询（集成CoinGecko/Jupiter Price API）
- [ ] 交易历史查询和解析
- [ ] WebSocket实时数据订阅

## 测试

```bash
# 运行单元测试
pytest tests/

# 测试RPC连接
python -m blockchain.solana.rpc_client
```

## 注意事项

1. **RPC限流**：免费RPC节点有请求限制，生产环境建议使用付费节点或自建
2. **交易确认**：Solana交易需要等待确认，建议使用WebSocket监听状态
3. **滑点保护**：代币兑换时务必设置合理的滑点容忍度
4. **安全审计**：DeFi操作涉及资金安全，上线前必须进行安全审计
