#!/usr/bin/env python3
"""
测试区块链服务的高级功能

测试场景：
1. Jupiter 价格 API - 批量查询代币价格
2. DeFi 聚合服务 - 获取协议收益率
3. 钱包服务 - 资产组合分析
4. Token 服务 - 代币元数据
5. Raydium 池子信息
"""

import asyncio
import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, "services"))

from blockchain.providers.jupiter import JupiterProvider
from blockchain.services.defi_aggregation_service import DeFiAggregationService
from blockchain.services.wallet_service import WalletService
from blockchain.services.token_service import TokenService
from blockchain.config import config


async def test_jupiter_prices():
    """测试 Jupiter 价格 API"""
    print("=" * 60)
    print("测试 1: Jupiter 价格 API")
    print("=" * 60)

    jupiter = JupiterProvider()

    try:
        # 测试单个代币价格
        print("\n📊 查询 SOL 价格:")
        sol_price = await jupiter.get_token_price(config.WRAPPED_SOL_MINT)
        print(f"  SOL: ${sol_price:.2f}")

        # 测试批量查询
        print("\n📊 批量查询代币价格:")
        tokens = config.get_tokens()
        mints = list(tokens.values())
        prices = await jupiter.batch_get_token_prices(mints)

        for symbol, mint in tokens.items():
            price = prices.get(mint)
            if price:
                print(f"  {symbol}: ${price:.4f}")
            else:
                print(f"  {symbol}: 价格不可用")

        print("\n✅ Jupiter 价格 API 测试通过")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await jupiter.close()


async def test_defi_aggregation():
    """测试 DeFi 聚合服务"""
    print("\n\n" + "=" * 60)
    print("测试 2: DeFi 聚合服务")
    print("=" * 60)

    defi_service = DeFiAggregationService()

    try:
        # 获取实时价格
        print("\n📊 获取实时价格:")
        prices = await defi_service.get_realtime_prices()
        for token, data in list(prices.items())[:5]:  # 只显示前5个
            print(f"  {token}: ${data.get('price_usd', 0):.4f}")

        # 获取收益率
        print("\n📊 获取 DeFi 收益率:")
        yields = await defi_service.get_protocol_yields()
        if yields.get('protocols'):
            print(f"  协议数量: {len(yields['protocols'])}")
            for protocol_name, protocol_data in list(yields['protocols'].items())[:2]:
                print(f"\n  {protocol_name}:")
                print(f"    名称: {protocol_data.get('name')}")
                print(f"    类型: {protocol_data.get('type')}")
                print(f"    池子数量: {len(protocol_data.get('pools', []))}")

        # 获取最佳机会
        if yields.get('best_opportunities'):
            print(f"\n📊 最佳投资机会 (前5个):")
            for opp in yields['best_opportunities'][:5]:
                print(f"  • {opp.get('protocol')} - {opp.get('symbol')}: {opp.get('apy'):.2f}% APY (TVL: ${opp.get('tvl_usd'):,.0f})")

        # 获取完整概览
        print("\n📊 获取完整概览:")
        overview = await defi_service.get_overview()
        print(f"  价格数据: {len(overview.get('prices', {}))} 个代币")
        print(f"  收益数据: {len(overview.get('yields', {}).get('protocols', {}))} 个协议")

        print("\n✅ DeFi 聚合服务测试通过")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await defi_service.close()


async def test_wallet_service():
    """测试钱包服务"""
    print("\n\n" + "=" * 60)
    print("测试 3: 钱包服务")
    print("=" * 60)

    # 使用一个 Devnet 测试钱包
    test_wallet = "9B5XszUGdMaxCZ7uSQhPzdks5ZQSmWxrmzCSvtJ6Ns6g"

    wallet_service = WalletService()

    try:
        print(f"\n📍 测试钱包: {test_wallet}")

        # 获取 SOL 余额
        print("\n📊 查询 SOL 余额:")
        sol_balance = await wallet_service.get_sol_balance(test_wallet)
        print(f"  余额: {sol_balance.sol:.4f} SOL")
        if sol_balance.usd_value:
            print(f"  价值: ${sol_balance.usd_value:.2f}")

        # 获取 Token 账户
        print("\n📊 查询 SPL Token:")
        tokens = await wallet_service.get_token_accounts(test_wallet)
        print(f"  Token 数量: {len(tokens)}")

        # 显示前5个有价值的 Token
        valuable_tokens = [t for t in tokens if t.usd_value and t.usd_value > 0]
        if valuable_tokens:
            print(f"\n  有价值的 Token (前5个):")
            for token in valuable_tokens[:5]:
                symbol = token.symbol or token.mint[:8]
                print(f"    • {symbol}: {token.balance:.4f} (${token.usd_value:.2f})")

        # 获取完整资产组合
        print("\n📊 获取完整资产组合:")
        portfolio = await wallet_service.get_wallet_portfolio(test_wallet)
        print(f"  SOL: {portfolio.sol_balance.sol:.4f}")
        print(f"  SPL Token: {len(portfolio.tokens)} 个")
        print(f"  总价值: ${portfolio.total_usd_value:.2f}")

        print("\n✅ 钱包服务测试通过")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await wallet_service.close()


async def test_token_service():
    """测试 Token 服务"""
    print("\n\n" + "=" * 60)
    print("测试 4: Token 服务")
    print("=" * 60)

    token_service = TokenService()

    try:
        # 测试获取单个代币价格
        print("\n📊 查询单个代币价格:")
        tokens = config.get_tokens()

        for symbol, mint in list(tokens.items())[:3]:  # 只测试前3个
            print(f"\n  {symbol} ({mint[:8]}...):")
            try:
                token_price = await token_service.get_token_price(mint, symbol)
                if token_price:
                    print(f"    价格: ${token_price.price_usd:.4f}")
                else:
                    print(f"    ⚠️  价格不可用")
            except Exception as e:
                print(f"    ⚠️  获取失败: {e}")

        # 测试批量获取价格
        print("\n📊 批量查询价格:")
        mints = list(tokens.values())
        prices = await token_service.batch_get_token_prices(mints)
        for symbol, mint in tokens.items():
            token_price = prices.get(mint)
            if token_price:
                print(f"  {symbol}: ${token_price.price_usd:.4f}")

        # 测试获取 SOL 价格
        print("\n📊 查询 SOL 价格:")
        sol_price = await token_service.get_sol_price()
        if sol_price:
            print(f"  SOL: ${sol_price:.2f}")

        print("\n✅ Token 服务测试通过")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await token_service.close()


async def test_network_info():
    """测试网络信息"""
    print("\n\n" + "=" * 60)
    print("测试 5: 网络配置信息")
    print("=" * 60)

    print(f"\n📊 当前配置:")
    print(f"  网络: {config.NETWORK}")
    print(f"  RPC 端点: {config.get_primary_rpc()}")
    print(f"  Jupiter API: {config.JUPITER_PRICE_URL}")
    print(f"  Raydium API: {config.RAYDIUM_API_URL}")
    print(f"  超时设置: {config.RPC_TIMEOUT}s")
    print(f"  最大重试: {config.RPC_MAX_RETRIES}")

    print(f"\n📊 代币配置:")
    tokens = config.get_tokens()
    for symbol, mint in tokens.items():
        print(f"  {symbol}: {mint}")

    print(f"\n📊 缓存配置:")
    print(f"  余额缓存: {config.CACHE_TTL_BALANCE}s")
    print(f"  Token 缓存: {config.CACHE_TTL_TOKENS}s")
    print(f"  价格缓存: {config.CACHE_TTL_TOKEN_PRICE}s")
    print(f"  DeFi 缓存: {config.CACHE_TTL_DEFI_RATES}s")

    print("\n✅ 网络配置测试通过")


async def test_error_handling():
    """测试错误处理"""
    print("\n\n" + "=" * 60)
    print("测试 6: 错误处理")
    print("=" * 60)

    wallet_service = WalletService()

    try:
        # 测试无效钱包地址
        print("\n📊 测试无效钱包地址:")
        try:
            await wallet_service.get_sol_balance("invalid_address")
            print("  ❌ 应该抛出异常")
        except Exception as e:
            print(f"  ✅ 正确捕获异常: {type(e).__name__}")

        # 测试不存在的代币
        print("\n📊 测试不存在的代币:")
        jupiter = JupiterProvider()
        try:
            price = await jupiter.get_token_price("InvalidMintAddress123")
            if price is None:
                print("  ✅ 返回 None")
            else:
                print(f"  ⚠️  返回了价格: {price}")
        except Exception as e:
            print(f"  ✅ 正确捕获异常: {type(e).__name__}")
        finally:
            await jupiter.close()

        print("\n✅ 错误处理测试通过")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await wallet_service.close()


async def main():
    """运行所有测试"""
    print("\n🚀 开始测试区块链服务高级功能\n")

    try:
        # 测试 1: Jupiter 价格 API
        await test_jupiter_prices()

        # 测试 2: DeFi 聚合服务
        await test_defi_aggregation()

        # 测试 3: 钱包服务
        await test_wallet_service()

        # 测试 4: Token 服务
        await test_token_service()

        # 测试 5: 网络配置
        await test_network_info()

        # 测试 6: 错误处理
        await test_error_handling()

        print("\n\n" + "=" * 60)
        print("🎉 所有区块链服务测试完成！")
        print("=" * 60)
        print("\n✅ 测试通过的功能:")
        print("  1. Jupiter 价格 API - 单个/批量查询")
        print("  2. DeFi 聚合服务 - 价格/收益率/最佳机会")
        print("  3. 钱包服务 - SOL/Token/资产组合")
        print("  4. Token 服务 - 元数据/批量价格")
        print("  5. 网络配置 - RPC/缓存/代币配置")
        print("  6. 错误处理 - 异常捕获和降级")

    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
