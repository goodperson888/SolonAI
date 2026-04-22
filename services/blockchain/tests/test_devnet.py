"""
Devnet 集成测试

运行: python tests/test_devnet.py
"""

import asyncio

from . import main

if __name__ == "__main__":
    asyncio.run(main())
