# DeFi 协议指南

## Jupiter DEX 聚合器
Jupiter 是 Solana 上最大的 DEX 聚合器，聚合多个 DEX 的流动性找到最优价格。功能包括：即时 Swap（代币兑换）、限价单、DCA 定投、永续合约交易。代币是 JUP。建议滑点设置 0.5%-1%。交易费约 0.3%-0.5% + 极低网络费。大额交易建议分批执行以减少滑点影响。Jupiter API 可编程调用获取报价和构建交易。

## Raydium AMM
Raydium 是 Solana 上的 AMM 和流动性协议。提供自动做市商（AMM）交易，支持集中流动性（CLMM）和标准流动性池。流动性提供者（LP）可以赚取交易手续费。代币是 RAY。常见池子有 SOL/USDC、RAY/USDC、SOL/RAY。APY 范围 5%-50%。主要风险是无常损失，建议选择稳定币对降低风险。

## Orca DEX
Orca 是 Solana 上用户友好的 DEX，使用 Whirlpool 集中流动性机制。界面简洁适合新手，支持集中流动性范围设置。代币是 ORCA。优势包括低滑点和 MEV 保护。流动性提供 APY 10%-100%，集中流动性范围越窄收益越高但风险也越高。需要注意范围外流动性不产生收益，需定期调整范围。

## MarginFi 借贷协议
MarginFi 是 Solana 上的主要借贷协议。支持存款赚利息和抵押借款。支持的资产包括 SOL、USDC、USDT、mSOL、JitoSOL 等。存款 APY：SOL 约 5-8%，USDC 约 3-6%。借款利率：SOL 约 8-15%，USDC 约 5-10%。健康度（Health Factor）大于 1 表示安全，低于 1 会被清算，清算惩罚约 5-10%。建议保持健康度在 1.5 以上。

## Kamino Finance
Kamino 是 Solana 上的自动化 DeFi 协议。提供自动化流动性管理策略，自动调整集中流动性范围。支持借贷（Kamino Lend）和杠杆策略。优势是自动复利，免除手动管理。APY 范围 10%-50%。管理费约 10% 的收益。主要风险包括智能合约风险和无常损失。

## Marinade Finance
Marinade 是 Solana 上最大的流动性质押协议。质押 SOL 获得 mSOL，mSOL 可在 DeFi 中继续使用。原生质押 APY 约 6.5-7%。Marinade Native 无需支付手续费。mSOL 可以作为抵押品在 MarginFi 等借贷协议中使用，实现收益叠加。

## Jito
Jito 是 Solana 上的 MEV 相关质押协议。质押 SOL 获得 JitoSOL，除了基础质押收益外还包含 MEV 收益。APY 约 7-8%，通常高于普通质押。JitoSOL 同样可以在 DeFi 中使用。Jito 还提供区块空间拍卖服务。
