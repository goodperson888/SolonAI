"""
HTTP 请求容错工具

提供带重试的 HTTP 客户端封装，用于 Jupiter / Raydium / MarginFi 等外部 API
"""

import asyncio
import logging
from typing import Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class ResilientHTTPClient:
    """
    带重试和容错的 HTTP 客户端

    特性：
    - 自动重试（指数退避）
    - 超时控制
    - 429 限流自动等待
    - 可配置重试条件
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        headers: Optional[Dict[str, str]] = None,
    ):
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=headers or {"Accept": "application/json"},
        )

    async def get(self, url: str, **kwargs) -> httpx.Response:
        """带重试的 GET 请求"""
        return await self._request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        """带重试的 POST 请求"""
        return await self._request("POST", url, **kwargs)

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """核心请求方法，带重试逻辑"""
        last_error = None

        for attempt in range(self._max_retries):
            try:
                response = await self._client.request(method, url, **kwargs)

                # 429 限流：等待后重试
                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", "2"))
                    logger.warning(
                        f"HTTP 429 限流 [{url[:50]}...], 等待 {retry_after}s "
                        f"(尝试 {attempt + 1}/{self._max_retries})"
                    )
                    if attempt < self._max_retries - 1:
                        await asyncio.sleep(retry_after)
                        continue

                # 5xx 服务端错误：重试
                if response.status_code >= 500:
                    logger.warning(
                        f"HTTP {response.status_code} [{url[:50]}...] "
                        f"(尝试 {attempt + 1}/{self._max_retries})"
                    )
                    if attempt < self._max_retries - 1:
                        delay = self._retry_delay * (2**attempt)
                        await asyncio.sleep(delay)
                        continue

                # 其他状态码（含成功和 4xx）直接返回
                return response

            except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                last_error = e
                logger.warning(
                    f"HTTP 连接失败 [{url[:50]}...] (尝试 {attempt + 1}/{self._max_retries}): {e}"
                )
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (2**attempt)
                    await asyncio.sleep(delay)

            except httpx.ReadTimeout as exc:
                last_error = exc
                logger.warning(
                    f"HTTP 读取超时 [{url[:50]}...] (尝试 {attempt + 1}/{self._max_retries})"
                )
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (2**attempt)
                    await asyncio.sleep(delay)

            except Exception:
                # 其他异常不重试
                raise

        # 所有重试耗尽
        if last_error:
            raise last_error
        raise httpx.ConnectError(f"所有 {self._max_retries} 次重试均失败: {url}")

    async def close(self):
        """关闭客户端"""
        await self._client.aclose()
