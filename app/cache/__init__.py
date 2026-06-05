"""
Redis 缓存模块

提供统一的缓存接口，支持：
- 多级缓存键管理
- JSON 序列化/反序列化
- 基于模式匹配的批量失效
- 装饰器缓存
- 分布式缓存扩展预留

使用示例:
    from app.cache import cache_manager, cached, invalidate_pattern

    # 基础使用
    cache_manager.set("user:1", user_data, ttl=300)
    data = cache_manager.get("user:1")
    cache_manager.delete("user:1")

    # 装饰器模式
    @cached(ttl=300, prefix="property")
    def get_property(property_id: int):
        ...

    # 批量失效
    invalidate_pattern("property:*")
"""

from app.cache.cache_manager import cache_manager
from app.cache.decorators import cached, cache_invalidate
from app.cache.invalidation import (
    invalidate_property_cache,
    invalidate_news_cache,
    invalidate_booking_cache,
    invalidate_contract_cache,
    invalidate_user_cache,
    invalidate_all_stats,
)
from app.cache.key_builder import CacheKey

__all__ = (
    "cache_manager",
    "cached",
    "cache_invalidate",
    "CacheKey",
    "invalidate_property_cache",
    "invalidate_news_cache",
    "invalidate_booking_cache",
    "invalidate_contract_cache",
    "invalidate_user_cache",
    "invalidate_all_stats",
)