"""
Devnet 集成测试

测试 Solana RPC + Jupiter + Raydium 全链路功能
使用 Devnet 测试币，无需真实资金

运行方式:
    cd services/blockchain
    python -m pytest tests/test_devnet.py -v -s
    # 或直接运行:
    python tests/test_devnet.py
"""

import asyncio
import os
import sys

# 确保能找到包
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


async def test_rpc_client():
    """测试 RPC 客户端基础功能"""
    from blockchain.transport.rpc_client import EnhancedRPCClient

    print("\n" + "=" * 60)
    print("  测试 1: RPC 客户端基础功能")
    print("=" * 60)

    client = EnhancedRPCClient()

    # 1. 获取最新 blockhash
    print("\n📦 获取最新 blockhash...")
    blockhash = await client.get_latest_blockhash()
    print(f"  ✅ Blockhash: {blockhash}")
    assert blockhash, "Blockhash 不应为空"

    # 2. 请求 airdrop（Devnet）
    # 使用一个固定的测试地址
    test_address = "vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg"
    print(f"\n💰 查询测试地址余额: {test_address[:16]}...")
    balance = await client.get_balance(test_address)
    print(f"  ✅ 余额: {balance} lamports ({balance / 1e9:.4f} SOL)")

    # 3. 获取 Token 账户
    print("\n🪙 查询 Token 账户...")
    tokens = await client.get_token_accounts_parsed(test_address)
    print(f"  ✅ 找到 {len(tokens)} 个 Token 账户")
    for t in tokens[:3]:
        print(f"     - Mint: {t['mint'][:16]}... 余额: {t['balance']}")

    await client.close()
    print("\n  ✅ RPC 客户端测试通过!")
    return True


async def test_wallet_service():
    """测试钱包服务"""
    from blockchain.services.wallet_service import WalletService

    print("\n" + "=" * 60)
    print("  测试 2: 钱包资产查询服务")
    print("=" * 60)

    service = WalletService()
    test_address = "vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg"

    # 1. SOL 余额
    print("\n💎 获取 SOL 余额...")
    sol_balance = await service.get_sol_balance(test_address)
    print(f"  ✅ SOL: {sol_balance.sol}")
    if sol_balance.usd_value:
        print(f"  ✅ USD: ${sol_balance.usd_value:.2f}")
    else:
        print("  ⚠️  USD 估值不可用（Devnet 代币无价格）")

    # 2. 资产全景
    print("\n📊 获取资产全景...")
    portfolio = await service.get_wallet_portfolio(test_address)
    print(f"  ✅ SOL: {portfolio.sol_balance.sol}")
    print(f"  ✅ Token 数量: {len(portfolio.tokens)}")
    print(f"  ✅ 总价值: ${portfolio.total_usd_value:.2f}")

    await service.close()
    print("\n  ✅ 钱包服务测试通过!")
    return True


async def test_jupiter_provider():
    """测试 Jupiter 协议"""
    from blockchain.config import config
    from blockchain.providers.jupiter import JupiterProvider

    print("\n" + "=" * 60)
    print("  测试 3: Jupiter 聚合交易协议")
    print("=" * 60)

    jupiter = JupiterProvider()
    # Jupiter API 只支持 Mainnet 代币，始终使用 Mainnet 地址
    tokens = config.MAINNET_TOKENS

    # 1. SOL 价格查询
    print("\n💲 查询 SOL 价格...")
    sol_price = await jupiter.get_token_price(config.WRAPPED_SOL_MINT)
    if sol_price:
        print(f"  ✅ SOL 价格: ${sol_price:.2f}")
    else:
        print("  ⚠️  SOL 价格不可用")

    # 2. Swap 报价 (SOL → USDC)
    print("\n🔄 获取 SOL → USDC 报价 (0.1 SOL)...")
    try:
        amount_lamports = 100_000_000  # 0.1 SOL
        quote = await jupiter.get_swap_quote(
            input_mint=tokens["SOL"],
            output_mint=tokens["USDC"],
            amount=amount_lamports,
            slippage_bps=50,
        )
        print(f"  ✅ 输入: {quote.in_amount} lamports")
        print(f"  ✅ 输出: {quote.out_amount} (最小单位)")
        print(f"  ✅ 价格影响: {quote.price_impact_pct}%")
        print(f"  ✅ 路由数: {len(quote.routes)}")

        # 3. 构建 swap 交易
        print("\n🔨 构建 Swap 交易...")
        test_wallet = "vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg"
        try:
            tx_base64 = await jupiter.build_swap_transaction(quote, test_wallet)
            print(f"  ✅ 交易数据长度: {len(tx_base64)} 字符")
            print(f"  ✅ 交易数据前缀: {tx_base64[:40]}...")
        except Exception as e:
            print(f"  ⚠️  交易构建失败（Devnet 流动性可能不足）: {e}")
            await jupiter.close()
            raise

    except Exception as e:
        print(f"  ❌ 报价获取失败: {e}")
        await jupiter.close()
        raise

    await jupiter.close()
    print("\n  ✅ Jupiter 测试完成!")
    return True


async def test_raydium_provider():
    """测试 Raydium 协议"""
    from blockchain.config import config
    from blockchain.providers.raydium import RaydiumProvider

    print("\n" + "=" * 60)
    print("  测试 4: Raydium AMM 协议")
    print("=" * 60)

    raydium = RaydiumProvider()

    # 1. 查询池列表（Mainnet API）
    print("\n🏊 查询 Raydium 池列表...")
    pools = await raydium.get_pool_list(page_size=5)
    print(f"  ✅ 获取到 {len(pools)} 个池")
    for pool in pools[:3]:
        pool_name = pool.get("poolName", "Unknown")
        tvl = pool.get("tvl", 0)
        print(f"     - {pool_name}: TVL ${tvl:,.0f}")

    # 2. Swap 报价 (SOL → USDC, Mainnet tokens)
    print("\n🔄 获取 Raydium SOL → USDC 报价 (0.1 SOL)...")
    try:
        # 使用 Mainnet 代币地址测试（Raydium Trade API 主要靠 Mainnet）
        mainnet_tokens = config.MAINNET_TOKENS
        amount_lamports = 100_000_000  # 0.1 SOL
        quote = await raydium.get_swap_quote(
            input_mint=mainnet_tokens["SOL"],
            output_mint=mainnet_tokens["USDC"],
            amount=amount_lamports,
            slippage_bps=50,
        )
        print(f"  ✅ 输入: {quote.in_amount} lamports")
        print(f"  ✅ 输出: {quote.out_amount} (USDC 最小单位)")
        print(f"  ✅ 价格影响: {quote.price_impact_pct}%")
    except Exception as e:
        print(f"  ❌ Raydium 报价失败: {e}")
        await raydium.close()
        raise

    await raydium.close()
    print("\n  ✅ Raydium 测试完成!")
    return True


async def test_transaction_service():
    """测试交易聚合服务"""
    from blockchain.config import config
    from blockchain.services.transaction_service import TransactionService

    print("\n" + "=" * 60)
    print("  测试 5: 交易聚合服务（最优报价）")
    print("=" * 60)

    service = TransactionService()
    mainnet_tokens = config.MAINNET_TOKENS

    # 聚合报价 (auto 模式)
    print("\n🏆 获取最优 SOL → USDC 报价 (0.1 SOL)...")
    try:
        quote = await service.get_swap_quote(
            input_mint=mainnet_tokens["SOL"],
            output_mint=mainnet_tokens["USDC"],
            amount=100_000_000,
            slippage_bps=50,
            provider="auto",
        )
        print(f"  ✅ 最优来源: {quote.provider}")
        print(f"  ✅ 输入: {quote.in_amount} lamports (0.1 SOL)")
        print(f"  ✅ 输出: {quote.out_amount} (USDC 最小单位)")
        print(f"  ✅ 价格影响: {quote.price_impact_pct}%")
    except Exception as e:
        print(f"  ❌ 聚合报价失败: {e}")
        await service.close()
        raise

    await service.close()
    print("\n  ✅ 交易聚合服务测试完成!")
    return True


async def test_airdrop():
    """测试 Devnet Airdrop"""
    from blockchain.transport.rpc_client import EnhancedRPCClient

    print("\n" + "=" * 60)
    print("  测试 6: Devnet Airdrop")
    print("=" * 60)

    client = EnhancedRPCClient()

    # 生成临时测试地址
    from solders.keypair import Keypair

    kp = Keypair()
    address = str(kp.pubkey())
    print(f"\n🔑 测试地址: {address}")

    # Airdrop
    print("\n🪂 请求 Airdrop 1 SOL...")
    try:
        sig = await client.request_airdrop(address, 1_000_000_000)
        print(f"  ✅ Airdrop 签名: {sig}")

        # 等待确认
        print("  ⏳ 等待确认...")
        await asyncio.sleep(3)

        balance = await client.get_balance(address)
        print(f"  ✅ 余额: {balance / 1e9:.4f} SOL")
    except Exception as e:
        print(f"  ❌ Airdrop 失败: {e}")
        await client.close()
        raise

    await client.close()
    print("\n  ✅ Airdrop 测试完成!")
    return True


async def main():
    """运行所有测试"""
    print("\n" + "🚀" * 30)
    print("  Solon AI — Blockchain Service 集成测试")
    print("  网络: Devnet")
    print("🚀" * 30)

    results = {}

    all_passed = True

    for name, test_func in [
        ("RPC 客户端", test_rpc_client),
        ("钱包服务", test_wallet_service),
        ("Jupiter", test_jupiter_provider),
        ("Raydium", test_raydium_provider),
        ("交易聚合", test_transaction_service),
        ("Airdrop", test_airdrop),
    ]:
        try:
            await test_func()
            results[name] = "✅ 通过"
        except Exception as e:
            results[name] = f"❌ 失败: {e}"
            all_passed = False
            import traceback

            traceback.print_exc()

    # 汇总
    print("\n" + "=" * 60)
    print("  测试汇总")
    print("=" * 60)
    for name, status in results.items():
        print(f"  {status}  {name}")
    print("=" * 60)

    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
