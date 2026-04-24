"""
MarginFi 集成测试

测试 MarginFi Provider（真实实现）和 MarginFi Client（stub 检测）

运行方式:
    cd services/blockchain
    python tests/test_marginfi.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


async def _test_marginfi_provider_lending_pools():
    """测试 MarginFi Provider — get_lending_pools()"""
    from blockchain.providers.marginfi import MarginFiProvider

    print("\n" + "=" * 60)
    print("  测试 1: MarginFi Provider — 借贷池查询")
    print("=" * 60)

    provider = MarginFiProvider()

    print("\n🏦 获取 MarginFi 借贷池...")
    pools = await provider.get_lending_pools()
    print(f"  ✅ 获取到 {len(pools)} 个借贷池")
    assert len(pools) > 0, "借贷池列表不应为空"

    data_source = "fallback"

    for pool in pools:
        if pool.deposit_apy > 0 or pool.total_deposits > 0:
            data_source = "RPC/DeFiLlama"
        print(
            f"     - {pool.symbol:8s} | "
            f"存款APY: {float(pool.deposit_apy):6.2f}% | "
            f"借款APY: {float(pool.borrow_apy):6.2f}% | "
            f"TVL: ${float(pool.total_deposits):,.0f} | "
            f"利用率: {float(pool.utilization_rate):.1f}%"
        )
    print(f"\n  📊 数据来源: {data_source}")
    assert len(pools) >= 5, f"应至少包含 5 个已知池，实际: {len(pools)}"

    await provider.close()
    print("  ✅ MarginFi 借贷池测试通过!")
    return True, data_source


async def _test_marginfi_provider_user_positions():
    """测试 MarginFi Provider — get_user_positions()"""
    from blockchain.providers.marginfi import MarginFiProvider

    print("\n" + "=" * 60)
    print("  测试 2: MarginFi Provider — 用户仓位查询")
    print("=" * 60)

    provider = MarginFiProvider()

    # 用系统程序地址测试（不会有 MarginFi 账户）
    test_addr = "11111111111111111111111111111111"
    print(f"\n👤 查询用户仓位 ({test_addr[:16]}...)...")
    positions = await provider.get_user_positions(test_addr)
    print(f"  ✅ 返回 {len(positions)} 个仓位（预期为空）")
    assert isinstance(positions, list), "应返回列表"

    await provider.close()
    print("  ✅ 用户仓位查询测试通过!")
    return True


async def _test_marginfi_provider_parse_i80f48():
    """测试 MarginFi Provider — I80F48 解析"""
    from blockchain.providers.marginfi import MarginFiProvider

    print("\n" + "=" * 60)
    print("  测试 3: MarginFi Provider — I80F48 定点数解析")
    print("=" * 60)

    # 零值
    result = MarginFiProvider._parse_i80f48(b"\x00" * 16)
    print(f"  零值解析: {result}")
    assert result == 0.0, f"零值应为 0.0, 得到 {result}"

    # 1.0 = 2^48 in I80F48
    one_encoded = (1 << 48).to_bytes(16, byteorder="little", signed=False)
    result = MarginFiProvider._parse_i80f48(one_encoded)
    print(f"  1.0 解析: {result}")
    assert abs(result - 1.0) < 0.0001, f"1.0 编码应解析为 ~1.0, 得到 {result}"

    # 错误长度
    result = MarginFiProvider._parse_i80f48(b"\x00" * 8)
    print(f"  错误长度: {result}")
    assert result == 0.0, "错误长度应返回 0.0"

    print("  ✅ I80F48 解析测试通过!")
    return True


async def _test_marginfi_provider_swap_rejected():
    """测试 MarginFi Provider — Swap 应被拒绝"""
    from blockchain.exceptions import ProviderError
    from blockchain.providers.marginfi import MarginFiProvider

    print("\n" + "=" * 60)
    print("  测试 4: MarginFi Provider — Swap 拒绝")
    print("=" * 60)

    provider = MarginFiProvider()

    print("\n🚫 调用 get_swap_quote (应抛出 ProviderError)...")
    try:
        await provider.get_swap_quote("SOL", "USDC", 100000000)
        print("  ❌ 未抛出异常!")
        await provider.close()
        return False
    except ProviderError as e:
        print(f"  ✅ 正确抛出 ProviderError: {e}")
        await provider.close()
        return True
    except Exception as e:
        print(f"  ⚠️  抛出了非预期异常: {type(e).__name__}: {e}")
        await provider.close()
        return False


def test_marginfi_provider_lending_pools():
    """pytest 入口：运行 MarginFi 借贷池查询测试"""
    asyncio.run(_test_marginfi_provider_lending_pools())


def test_marginfi_provider_user_positions():
    """pytest 入口：运行 MarginFi 用户仓位查询测试"""
    asyncio.run(_test_marginfi_provider_user_positions())


def test_marginfi_provider_parse_i80f48():
    """pytest 入口：运行 I80F48 解析测试"""
    asyncio.run(_test_marginfi_provider_parse_i80f48())


def test_marginfi_provider_swap_rejected():
    """pytest 入口：运行 Swap 拒绝测试"""
    asyncio.run(_test_marginfi_provider_swap_rejected())


async def main():
    """运行所有 MarginFi 测试"""
    print("\n" + "🏦" * 30)
    print("  Solon AI — MarginFi 集成测试")
    print("🏦" * 30)

    results = {}
    pool_source = "unknown"

    for name, test_func in [
        ("Provider: 借贷池查询", _test_marginfi_provider_lending_pools),
        ("Provider: 用户仓位查询", _test_marginfi_provider_user_positions),
        ("Provider: I80F48 解析", _test_marginfi_provider_parse_i80f48),
        ("Provider: Swap 拒绝", _test_marginfi_provider_swap_rejected),
    ]:
        try:
            result = await test_func()
            if isinstance(result, tuple):
                results[name] = "✅ 通过"
                pool_source = result[1]
            elif isinstance(result, list):
                results[name] = "✅ 通过"
                for func_name, status in result:
                    results[f"  Client.{func_name}"] = f"⚠️  {status}"
            elif result:
                results[name] = "✅ 通过"
            else:
                results[name] = "❌ 失败"
        except Exception as e:
            results[name] = f"❌ 失败: {e}"
            import traceback

            traceback.print_exc()

    # 汇总
    print("\n" + "=" * 60)
    print("  MarginFi 测试汇总")
    print("=" * 60)
    for name, status in results.items():
        print(f"  {status}  {name}")
    print(f"\n  📊 借贷池数据来源: {pool_source}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
