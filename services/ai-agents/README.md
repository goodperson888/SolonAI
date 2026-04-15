# AI Agents Service

多智能体协同服务，基于 LangGraph 实现。

## 架构

```
ai-agents/
├── agents/              # 各个智能体
│   ├── intent_agent.py          # 意图理解
│   ├── data_aggregation_agent.py # 链上数据聚合
│   ├── strategy_agent.py        # 策略生成
│   ├── risk_agent.py            # 风控审计
│   ├── execution_agent.py       # 执行协调
│   ├── monitoring_agent.py      # 监控与预警
│   ├── explanation_agent.py     # 自然语言解读
│   └── validation_agent.py      # 结果校验
├── graphs/              # LangGraph流程图
│   └── main_graph.py        # 主流程图
└── requirements.txt     # Python依赖
```

## 智能体职责

### IntentAgent (意图理解)
- 解析用户自然语言输入
- 识别用户意图类型
- 提取关键参数

### DataAggregationAgent (链上数据聚合) ⭐新增
- 实时获取链上数据
- 多源数据聚合与清洗
- 标准化处理

### StrategyAgent (策略生成)
- 根据用户意图生成DeFi策略
- 调用链上数据分析
- 优化策略参数

### RiskAgent (风控审计)
- 全流程风险把控
- 黑名单匹配
- 协议安全审计

### ExecutionAgent (执行协调)
- 将策略转换为交易指令
- 协调非托管执行流程
- 生成交易预览

### MonitoringAgent (监控与预警) ⭐新增
- 7*24小时监控策略执行
- 实时跟踪收益和风险
- 异常预警和调仓建议

### ExplanationAgent (自然语言解读) ⭐新增
- 把专业内容翻译成大白话
- 生成可视化报告
- 多轮对话答疑

### ValidationAgent (结果校验) ⭐新增
- 校验其他Agent输出的准确性
- 识别和拦截大模型幻觉
- 确保合规性

## 开发指南

### 环境配置

```bash
cd services/ai-agents
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 环境变量

创建 `.env` 文件：

```env
# LLM API配置
OPENAI_API_KEY=your_openai_key
# 或使用DeepSeek
DEEPSEEK_API_KEY=your_deepseek_key

# 数据库配置
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis配置
REDIS_URL=redis://host:6379
```

### 使用示例

```python
from ai_agents import MainGraph, IntentAgent, StrategyAgent, RiskAgent, ExecutionAgent

# 初始化智能体
agents = {
    "intent": IntentAgent(llm_client),
    "strategy": StrategyAgent(llm_client, data_service),
    "risk": RiskAgent(blacklist_db),
    "execution": ExecutionAgent(blockchain_service)
}

# 创建主流程图
main_graph = MainGraph(agents)

# 运行流程
result = await main_graph.run(
    user_input="帮我找一个稳健的收益策略",
    wallet_address="your_wallet_address"
)
```

## 待实现功能

- [ ] 完善意图理解的NLP模型
- [ ] 实现策略生成的优化算法
- [ ] 接入真实的黑名单数据库
- [ ] 实现交易构建和签名验证
- [ ] 添加监控和日志
- [ ] 添加单元测试
