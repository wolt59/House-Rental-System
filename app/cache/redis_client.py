"""
Redis 连接管理

负责 Redis 连接池的创建、连接生命周期管理以及健康检查。
支持优雅降级：当 Redis 不可用时，所有缓存操作静默跳过。
"""

import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("hrs.cache")

# 连接池实例（全局单例）
_pool: Optional = None
_client: Optional = None


def _import_redis():
    """延迟导入 redis 模块，避免启动时依赖检查失败"""
    try:
        import redis
        from redis import ConnectionPool, Redis
        logger.debug("Redis 模块导入成功: version=%s", redis.__version__)
        return redis, ConnectionPool, Redis
    except ImportError as e:
        logger.error("Redis 模块导入失败: %s", e)
        return None, None, None
    except Exception as e:
        logger.error("Redis 模块导入异常: %s", e)
        return None, None, None


def get_redis_pool():
    """获取或创建 Redis 连接池"""
    global _pool
    if _pool is None:
        redis_module, ConnectionPool, Redis = _import_redis()
        if redis_module is None:
            logger.warning("Redis 模块未安装，缓存功能已自动禁用")
            raise RuntimeError("Redis module not installed")
        _pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
            decode_responses=True,
        )
        logger.info("Redis 连接池已创建: %s, max_connections=%d", settings.REDIS_URL, settings.REDIS_MAX_CONNECTIONS)
    return _pool


def get_redis_client():
    """获取 Redis 客户端实例"""
    global _client
    if _client is None:
        _, _, Redis = _import_redis()
        if Redis is None:
            raise RuntimeError("Redis module not installed")
        pool = get_redis_pool()
        _client = Redis(connection_pool=pool)
    return _client


def close_redis() -> None:
    """关闭 Redis 连接池"""
    global _pool, _client
    if _client:
        _client.close()
        _client = None
    if _pool:
        _pool.disconnect()
        _pool = None
        logger.info("Redis 连接池已关闭")


def is_redis_available() -> bool:
    """检查 Redis 是否可用"""
    if not settings.CACHE_ENABLED:
        return False

    def _check():
        client = get_redis_client()
        return client.ping()

    result = safe_redis_call(_check)
    return result is not None and result is not False


def safe_redis_call(func, *args, **kwargs):
    """
    安全执行 Redis 操作，连接失败时优雅降级。

    返回:
        操作成功返回结果，失败返回 None
    """
    if not settings.CACHE_ENABLED:
        return None
    try:
        logger.debug("执行 Redis 操作")
        result = func(*args, **kwargs)
        logger.debug("Redis 操作成功")
        return result
    except Exception as e:
        exc_name = type(e).__name__
        exc_msg = str(e)
        if exc_name == "RuntimeError" and "not installed" in exc_msg:
            logger.warning("Redis 模块未安装，缓存功能已自动禁用")
        elif exc_name in ("ConnectionError", "TimeoutError", "ConnectionRefusedError"):
            logger.warning("Redis 服务器连接失败 (%s: %s)，缓存功能已自动降级", exc_name, exc_msg)
        else:
            logger.error("Redis 操作异常 (%s: %s)", exc_name, exc_msg)
            import traceback
            logger.error("完整堆栈: %s", traceback.format_exc())
        return None