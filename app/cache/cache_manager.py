"""
缓存管理器

提供核心缓存操作：get、set、delete、exists、invalidate_pattern。
所有操作均具备优雅降级能力，Redis 不可用时自动跳过。
"""

import logging
from typing import Any, Optional

from app.cache.redis_client import get_redis_client, safe_redis_call
from app.cache.serializer import serialize, deserialize
from app.core.config import settings

logger = logging.getLogger("hrs.cache")


class CacheManager:
    """
    缓存管理器（单例）

    提供统一的缓存读写接口，支持：
    - 键值对缓存
    - 批量模式失效
    - 命中率统计预留
    - 分布式缓存扩展预留
    """

    _instance: Optional["CacheManager"] = None

    def __new__(cls) -> "CacheManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ==================== 基础操作 ====================

    def get(self, key: str) -> Any:
        """
        从缓存获取数据。

        参数:
            key: 缓存键

        返回:
            缓存的数据，未命中或失败返回 None
        """
        if not settings.CACHE_ENABLED:
            return None

        def _get():
            client = get_redis_client()
            raw = client.get(key)
            if raw is None:
                return None
            return deserialize(raw)

        result = safe_redis_call(_get)
        if result is not None:
            logger.debug("缓存命中: %s", key)
        return result

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        向缓存写入数据。

        参数:
            key: 缓存键
            value: 要缓存的数据
            ttl: 过期时间（秒），默认使用 CACHE_DEFAULT_TTL

        返回:
            写入成功返回 True
        """
        if not settings.CACHE_ENABLED:
            return False

        serialized = serialize(value)
        if serialized is None:
            return False

        expire = ttl if ttl is not None else settings.CACHE_DEFAULT_TTL

        def _set():
            client = get_redis_client()
            client.setex(key, expire, serialized)

        result = safe_redis_call(_set)
        if result is not False:
            logger.debug("缓存写入: %s (ttl=%ds)", key, expire)
        return result is not False

    def delete(self, *keys: str) -> int:
        """
        删除指定缓存键。

        参数:
            keys: 要删除的缓存键

        返回:
            删除的键数量，失败返回 0
        """
        if not settings.CACHE_ENABLED or not keys:
            return 0

        def _delete():
            client = get_redis_client()
            return client.delete(*keys)

        result = safe_redis_call(_delete)
        count = result or 0
        if count > 0:
            logger.debug("缓存删除: %d 个键", count)
        return count

    def exists(self, key: str) -> bool:
        """检查缓存键是否存在"""
        if not settings.CACHE_ENABLED:
            return False

        def _exists():
            client = get_redis_client()
            return client.exists(key)

        result = safe_redis_call(_exists)
        return bool(result)

    def ttl(self, key: str) -> int:
        """获取缓存键的剩余过期时间（秒），-1 表示永不过期，-2 表示不存在"""
        if not settings.CACHE_ENABLED:
            return -2

        def _ttl():
            client = get_redis_client()
            return client.ttl(key)

        result = safe_redis_call(_ttl)
        return result if result is not None else -2

    # ==================== 批量操作 ====================

    def invalidate_pattern(self, pattern: str) -> int:
        """
        按模式批量失效缓存。

        使用 SCAN 命令避免阻塞，适用于生产环境。

        参数:
            pattern: Redis 键模式，如 "hrs:property:*"

        返回:
            删除的键数量
        """
        if not settings.CACHE_ENABLED:
            return 0

        def _invalidate():
            client = get_redis_client()
            count = 0
            cursor = 0
            while True:
                cursor, keys = client.scan(cursor, match=pattern, count=100)
                if keys:
                    count += client.delete(*keys)
                if cursor == 0:
                    break
            return count

        result = safe_redis_call(_invalidate)
        count = result or 0
        if count > 0:
            logger.info("缓存批量失效: pattern=%s, 删除 %d 个键", pattern, count)
        return count

    def flush_all(self) -> bool:
        """清空当前数据库的所有缓存（危险操作，仅用于开发/测试）"""
        if not settings.CACHE_ENABLED:
            return False

        def _flush():
            client = get_redis_client()
            client.flushdb()

        result = safe_redis_call(_flush)
        if result is not False:
            logger.warning("缓存已全部清空")
        return result is not False

    # ==================== 高级操作 ====================

    def get_or_set(
        self,
        key: str,
        factory: callable,
        ttl: Optional[int] = None,
        force_refresh: bool = False,
    ) -> Any:
        """
        从缓存获取数据，未命中时调用 factory 生成并写入缓存。

        参数:
            key: 缓存键
            factory: 数据生成函数（无参数）
            ttl: 过期时间
            force_refresh: 是否强制刷新缓存

        返回:
            缓存的数据或 factory 生成的数据
        """
        if not force_refresh:
            cached = self.get(key)
            if cached is not None:
                return cached

        try:
            data = factory()
        except Exception as e:
            logger.error("缓存 factory 执行失败: %s", e)
            raise

        if data is not None:
            self.set(key, data, ttl=ttl)
        return data

    def warm_up(self, key: str, factory: callable, ttl: Optional[int] = None) -> bool:
        """
        预热缓存（仅写入不读取）。

        适合在数据变更后异步刷新缓存。

        返回:
            写入成功返回 True
        """
        try:
            data = factory()
        except Exception as e:
            logger.error("缓存预热 factory 失败: %s", e)
            return False
        if data is not None:
            return self.set(key, data, ttl=ttl)
        return False


# 全局单例
cache_manager = CacheManager()