export const mockMessages = [
  {
    id: '1',
    role: 'assistant' as const,
    content:
      '你好！我是Solon AI，你的DeFi智能助手。我可以帮你分析资产、生成策略、执行交易。请问有什么可以帮到你的？',
    timestamp: new Date(Date.now() - 3600000),
  },
  {
    id: '2',
    role: 'user' as const,
    content: '帮我看看我的资产情况',
    timestamp: new Date(Date.now() - 3500000),
  },
  {
    id: '3',
    role: 'assistant' as const,
    content: `我已经分析了你的资产：

📊 总价值：$28,675.75
📈 24h涨跌：+3.8% (+$1,050.25)

主要持仓：
• SOL: 125.5枚 ($18,825.75)
• USDC: 5,000枚 ($5,000)
• JUP: 1,500枚 ($1,950)

建议：
1. SOL占比较高(65.6%)，可以考虑分散风险
2. USDC闲置较多，可以部署到稳定收益策略
3. 当前市场情绪良好，可以适当增加DeFi敞口`,
    timestamp: new Date(Date.now() - 3400000),
  },
  {
    id: '4',
    role: 'user' as const,
    content: '给我推荐一个低风险的策略',
    timestamp: new Date(Date.now() - 3300000),
  },
  {
    id: '5',
    role: 'assistant' as const,
    content: `根据你的需求，我推荐以下低风险策略：

💰 USDC稳定收益策略
协议：MarginFi
预期APY：8.5%
风险等级：低
锁定期：无

操作步骤：
1. 将3,000 USDC存入MarginFi
2. 获得存款凭证mUSDC
3. 自动复利

预期收益：
• 月收益：约$21.25
• 年收益：约$255

风险提示：
✓ 协议经过审计
✓ TVL超过$500M
✓ 无无常损失风险
⚠️ 存在智能合约风险

是否执行此策略？`,
    timestamp: new Date(Date.now() - 3200000),
  },
]
