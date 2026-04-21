# Solana 区块链基础知识

## 什么是 Solana
Solana 是一条高性能公链，采用 Proof of History (PoH) + Proof of Stake (PoS) 共识机制。出块时间约 400ms，交易确认极快，手续费极低（通常不到 0.01 美元）。原生代币是 SOL，用于支付手续费和质押。生态内有丰富的 DeFi、NFT、GameFi 应用。

## SOL 代币
SOL 是 Solana 的原生代币，主要用途包括：支付交易手续费、质押获取收益（年化约 6-8%）、治理投票。SOL 的最小单位是 lamport，1 SOL = 10^9 lamports。

## SPL Token 标准
SPL Token 是 Solana 上的代币标准，类似以太坊的 ERC-20。常见代币包括：USDC（Circle 发行的稳定币）、USDT（Tether 稳定币）、JUP（Jupiter 治理代币）、RAY（Raydium 治理代币）、ORCA（Orca 治理代币）。每个代币有唯一的 Mint 地址。转账需要关联代币账户（Associated Token Account）。

## 钱包
Solana 上常用的钱包有：Phantom（最流行，支持浏览器扩展和移动端）、Solflare（功能全面）、Backpack（新一代钱包）。钱包的核心是私钥，掌握私钥就掌握了资产控制权。助记词是私钥的人类可读形式，12或24个英文单词。切勿泄露私钥或助记词。

## 交易
Solana 交易特点：手续费约 0.000005 SOL（不到 0.01 美元），确认时间 1-2 秒。Token 转账需要 SOL 支付手续费，首次转账可能需要创建关联代币账户（约 0.002 SOL）。高峰期可设置优先费（Priority Fee）加速交易。所有交易都需要钱包签名确认。

## SOL 质押
SOL 质押方式分为：
1. 原生质押：选择验证者锁定 SOL，APY 约 6-8%，解质押需要等待约 2 天。
2. 流动性质押（推荐）：质押 SOL 获得流动性质押代币，可继续在 DeFi 中使用。主要有 mSOL（Marinade，APY 约 7%）、JitoSOL（Jito，APY 约 7.5%，含 MEV 收益）、bSOL（BlazeStake，APY 约 7%）。
3. 流动性质押代币可以继续存入借贷协议或做 LP，实现收益叠加。
