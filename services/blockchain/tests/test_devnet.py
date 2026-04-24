"""
Devnet 集成测试

运行: python tests/test_devnet.py
"""

import asyncio
import os
import sys

import pytest

if __package__ in (None, ""):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from blockchain.exceptions import RPCConnectionError, RPCTimeoutError
    from blockchain.tests import main
    from blockchain.tests import test_airdrop as _test_airdrop
    from blockchain.tests import test_jupiter_provider as _test_jupiter_provider
    from blockchain.tests import test_raydium_provider as _test_raydium_provider
    from blockchain.tests import test_rpc_client as _test_rpc_client
    from blockchain.tests import test_transaction_service as _test_transaction_service
    from blockchain.tests import test_wallet_service as _test_wallet_service
else:
    from ..exceptions import RPCConnectionError, RPCTimeoutError
    from . import main
    from . import test_airdrop as _test_airdrop
    from . import test_jupiter_provider as _test_jupiter_provider
    from . import test_raydium_provider as _test_raydium_provider
    from . import test_rpc_client as _test_rpc_client
    from . import test_transaction_service as _test_transaction_service
    from . import test_wallet_service as _test_wallet_service


def test_rpc_client():
    """pytest 入口：运行 RPC 客户端集成测试"""
    asyncio.run(_test_rpc_client())


def test_wallet_service():
    """pytest 入口：运行钱包服务集成测试"""
    asyncio.run(_test_wallet_service())


def test_jupiter_provider():
    """pytest 入口：运行 Jupiter 集成测试"""
    asyncio.run(_test_jupiter_provider())


def test_raydium_provider():
    """pytest 入口：运行 Raydium 集成测试"""
    asyncio.run(_test_raydium_provider())


def test_transaction_service():
    """pytest 入口：运行交易聚合集成测试"""
    asyncio.run(_test_transaction_service())


def test_airdrop():
    """pytest 入口：运行 Devnet Airdrop 集成测试。

    Devnet airdrop 依赖公共 RPC 可用性，网络不可达或节点临时异常时跳过。
    """
    try:
        asyncio.run(_test_airdrop())
    except (RPCConnectionError, RPCTimeoutError) as exc:
        pytest.skip(f"Devnet airdrop 当前不可用: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
