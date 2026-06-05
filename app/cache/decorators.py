"""
缓存装饰器

提供声明式的缓存集成方式，支持：
- 函数返回值自动缓存
- 基于参数动态生成缓存键
- 缓存失效触发
- 灵活的 TTL 配置
"""

import functools
import hashlib
import json
import logging
from typing import Any, Callable, Optional

from app.cache.cache_manager import cache_manager
from app.cache.serializer import CacheEncoder

logger = logging.getLogger("hrs.cache")


def _make_cache_key(prefix: str, args: tuple, kwargs: dict) -> str:
    """
    基于函数参数生成缓存键。

    排除第一参数 self/cls 和 db Session 对象。
    """
    filtered_kwargs = {}
    filtered_args = []

    for arg in args:
        # 跳过 SQLAlchemy Session 对象
        if hasattr(arg, "query") and hasattr(arg, "execute"):
            continue
        filtered_args.append(arg)

    for k, v in kwargs.items():
        if k == "db":
            continue
        if hasattr(v, "query") and hasattr(v, "execute"):
            continue
        filtered_kwargs[k] = v

    key_data = {
        "args": filtered_args,
        "kwargs": filtered_kwargs,
    }
    try:
        raw = json.dumps(key_data, cls=CacheEncoder, sort_keys=True, ensure_ascii=False)
    except TypeError:
        raw = str(filtered_args) + str(sorted(filtered_kwargs.items()))
    digest = hashlib.md5(raw.encode()).hexdigest()[:12]
    return f"decorator:{prefix}:{digest}"


def cached(
    ttl: Optional[int] = None,
    prefix: str = "func",
    key_builder: Optional[Callable] = None,
):
    """
    缓存装饰器：自动缓存函数返回值。

    使用方式:
        @cached(ttl=300, prefix="property")
        def get_property(property_id: int, db: Session):
            ...

    参数:
        ttl: 缓存过期时间（秒），默认使用全局配置 CACHE_DEFAULT_TTL
        prefix: 缓存键前缀，用于区分不同业务
        key_builder: 自定义缓存键生成函数，接收 (args, kwargs)，返回字符串
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = _make_cache_key(f"{prefix}:{func.__name__}", args, kwargs)

            # 检查是否强制刷新
            force_refresh = kwargs.pop("_cache_refresh", False)

            if not force_refresh:
                cached_result = cache_manager.get(cache_key)
                if cached_result is not None:
                    return cached_result

            result = func(*args, **kwargs)
            if result is not None:
                cache_manager.set(cache_key, result, ttl=ttl)
            return result

        # 附加缓存工具方法
        wrapper.cache_key_prefix = prefix
        wrapper.cache_ttl = ttl
        return wrapper

    return decorator


def cache_invalidate(patterns: list[str]):
    """
    缓存失效装饰器：在函数执行后批量失效缓存。

    使用方式:
        @cache_invalidate(["hrs:property:*", "hrs:stats:*"])
        def update_property(property_id: int, db: Session):
            ...

    参数:
        patterns: 要失效的缓存键模式列表
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            for pattern in patterns:
                count = cache_manager.invalidate_pattern(pattern)
                if count > 0:
                    logger.debug("自动失效缓存: pattern=%s, count=%d", pattern, count)
            return result

        return wrapper

    return decorator