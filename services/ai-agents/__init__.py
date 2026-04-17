"""
Solon AI - AI 智能体服务

8个 Agent 通过 LangGraph 协同工作：

1. IntentAgent      - 意图理解（入口）
2. DataAggregation  - 数据聚合
3. StrategyAgent    - 策略生成
4. RiskAgent        - 风控审计
5. ValidationAgent  - 结果验证
6. ExecutionAgent   - 执行协调
7. MonitoringAgent  - 持续监控
8. ExplanationAgent - 大白话解释（出口）

使用方法：
    from graphs.main_graph import run_agent

    result = await run_agent("帮我看看钱包里有什么资产")
    print(result["explanation"])
"""
