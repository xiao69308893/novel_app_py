
# app/utils/cache.py
# -*- coding: utf-8 -*-
"""
缓存工具
提供Redis缓存的封装和管理
"""

from typing import Any, Dict, List, Optional, Union
import json
import pickle
from datetime import datetime, timedelta
import redis.asyncio as redis
from loguru import logger

from app.config import settings


class CacheManager:
    """缓存管理器"""

    def __init__(self):
        """初始化缓存管理器"""
        self._redis_client: Optional[redis.Redis] = None
        self.key_prefix = settings.CACHE_KEY_PREFIX
        self.default_ttl = settings.CACHE_TTL

    @property
    async def redis(self) -> redis.Redis:
        """获取Redis连接"""
        if self._redis_client is None:
            self._redis_client = redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=False,  # 处理二进制数据
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                max_connections=settings.REDIS_CONNECTION_POOL_MAX
            )
        return self._redis_client

    def _make_key(self, key: str) -> str:
        """生成缓存键"""
        return f"{self.key_prefix}{key}"

    async def get(
            self,
            key: str,
            default: Any = None,
            serializer: str = "json"
    ) -> Any:
        """
        获取缓存值

        Args:
            key: 缓存键
            default: 默认值
            serializer: 序列化方式 (json/pickle)

        Returns:
            Any: 缓存值
        """

        try:
            redis_client = await self.redis
            cache_key = self._make_key(key)

            value = await redis_client.get(cache_key)
            if value is None:
                return default

            # 反序列化
            if serializer == "json":
                return json.loads(value)
            elif serializer == "pickle":
                return pickle.loads(value)
            else:
                return value.decode('utf-8') if isinstance(value, bytes) else value

        except Exception as e:
            logger.warning(f"缓存获取失败 {key}: {e}")
            return default

    async def set(
            self,
            key: str,
            value: Any,
            ttl: Optional[int] = None,
            serializer: str = "json"
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            serializer: 序列化方式 (json/pickle)

        Returns:
            bool: 设置成功
        """

        try:
            redis_client = await self.redis
            cache_key = self._make_key(key)
            expire_time = ttl or self.default_ttl

            # 序列化
            if serializer == "json":
                serialized_value = json.dumps(value, ensure_ascii=False)
            elif serializer == "pickle":
                serialized_value = pickle.dumps(value)
            else:
                serialized_value = str(value)

            await redis_client.setex(cache_key, expire_time, serialized_value)
            return True

        except Exception as e:
            logger.warning(f"缓存设置失败 {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            bool: 删除成功
        """

        try:
            redis_client = await self.redis
            cache_key = self._make_key(key)

            result = await redis_client.delete(cache_key)
            return result > 0

        except Exception as e:
            logger.warning(f"缓存删除失败 {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            bool: 是否存在
        """

        try:
            redis_client = await self.redis
            cache_key = self._make_key(key)

            result = await redis_client.exists(cache_key)
            return result > 0

        except Exception as e:
            logger.warning(f"缓存检查失败 {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """
        设置缓存过期时间

        Args:
            key: 缓存键
            ttl: 过期时间（秒）

        Returns:
            bool: 设置成功
        """

        try:
            redis_client = await self.redis
            cache_key = self._make_key(key)

            result = await redis_client.expire(cache_key, ttl)
            return result

        except Exception as e:
            logger.warning(f"缓存过期时间设置失败 {key}: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        递增缓存值

        Args:
            key: 缓存键
            amount: 递增量

        Returns:
            Optional[int]: 递增后的值
        """

        try:
            redis_client = await self.redis
            cache_key = self._make_key(key)

            result = await redis_client.incrby(cache_key, amount)
            return result

        except Exception as e:
            logger.warning(f"缓存递增失败 {key}: {e}")
            return None

    async def get_many(
            self,
            keys: List[str],
            serializer: str = "json"
    ) -> Dict[str, Any]:
        """
        批量获取缓存

        Args:
            keys: 缓存键列表
            serializer: 序列化方式

        Returns:
            Dict[str, Any]: 缓存值字典
        """

        try:
            redis_client = await self.redis
            cache_keys = [self._make_key(key) for key in keys]

            values = await redis_client.mget(cache_keys)

            result = {}
            for i, key in enumerate(keys):
                value = values[i]
                if value is not None:
                    if serializer == "json":
                        result[key] = json.loads(value)
                    elif serializer == "pickle":
                        result[key] = pickle.loads(value)
                    else:
                        result[key] = value.decode('utf-8') if isinstance(value, bytes) else value
                else:
                    result[key] = None

            return result

        except Exception as e:
            logger.warning(f"批量缓存获取失败: {e}")
            return {key: None for key in keys}

    async def set_many(
            self,
            mapping: Dict[str, Any],
            ttl: Optional[int] = None,
            serializer: str = "json"
    ) -> bool:
        """
        批量设置缓存

        Args:
            mapping: 键值对字典
            ttl: 过期时间
            serializer: 序列化方式

        Returns:
            bool: 设置成功
        """

        try:
            redis_client = await self.redis
            expire_time = ttl or self.default_ttl

            # 准备数据
            cache_data = {}
            for key, value in mapping.items():
                cache_key = self._make_key(key)

                if serializer == "json":
                    serialized_value = json.dumps(value, ensure_ascii=False)
                elif serializer == "pickle":
                    serialized_value = pickle.dumps(value)
                else:
                    serialized_value = str(value)

                cache_data[cache_key] = serialized_value

            # 批量设置
            async with redis_client.pipeline() as pipe:
                await pipe.mset(cache_data)

                # 设置过期时间
                for cache_key in cache_data.keys():
                    await pipe.expire(cache_key, expire_time)

                await pipe.execute()

            return True

        except Exception as e:
            logger.warning(f"批量缓存设置失败: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        根据模式删除缓存

        Args:
            pattern: 匹配模式

        Returns:
            int: 删除的数量
        """

        try:
            redis_client = await self.redis
            cache_pattern = self._make_key(pattern)

            # 查找匹配的键
            keys = await redis_client.keys(cache_pattern)

            if keys:
                deleted = await redis_client.delete(*keys)
                return deleted

            return 0

        except Exception as e:
            logger.warning(f"模式删除缓存失败 {pattern}: {e}")
            return 0

    async def clear_all(self) -> bool:
        """
        清空所有缓存

        Returns:
            bool: 清空成功
        """

        try:
            redis_client = await self.redis
            await redis_client.flushdb()
            return True

        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            return False


# 全局缓存管理器实例
cache_manager = CacheManager()


