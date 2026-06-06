"""
缓存失效辅助函数

提供业务级别的缓存失效触发，确保数据变更后缓存一致性。
"""

import logging

from app.cache.cache_manager import cache_manager
from app.cache.key_builder import CacheKey

logger = logging.getLogger("hrs.cache")


def invalidate_property_cache(property_id: int = None) -> int:
    """
    房源数据变更后失效相关缓存。

    参数:
        property_id: 具体房源 ID，为 None 时失效所有房源缓存

    返回:
        删除的缓存键总数
    """
    total = 0
    if property_id:
        total += cache_manager.delete(CacheKey.property(property_id))
    total += cache_manager.invalidate_pattern(CacheKey.pattern_all("property"))
    total += cache_manager.invalidate_pattern(CacheKey.pattern_all("stats"))
    if total > 0:
        logger.debug("房源缓存已失效: property_id=%s, total=%d", property_id, total)
    return total


def invalidate_news_cache(news_id: int = None) -> int:
    """
    新闻数据变更后失效相关缓存。

    参数:
        news_id: 具体新闻 ID，为 None 时失效所有新闻缓存

    返回:
        删除的缓存键总数
    """
    total = 0
    if news_id:
        total += cache_manager.delete(CacheKey.news(news_id))
    total += cache_manager.invalidate_pattern(CacheKey.pattern_all("news"))
    if total > 0:
        logger.debug("新闻缓存已失效: news_id=%s, total=%d", news_id, total)
    return total


def invalidate_booking_cache() -> int:
    """预约数据变更后失效相关缓存"""
    total = cache_manager.invalidate_pattern(CacheKey.pattern_all("booking"))
    total += cache_manager.invalidate_pattern(CacheKey.pattern_all("stats"))
    if total > 0:
        logger.debug("预约缓存已失效: total=%d", total)
    return total


def invalidate_contract_cache() -> int:
    """合同数据变更后失效相关缓存"""
    total = cache_manager.invalidate_pattern(CacheKey.pattern_all("contract"))
    total += cache_manager.invalidate_pattern(CacheKey.pattern_all("stats"))
    if total > 0:
        logger.debug("合同缓存已失效: total=%d", total)
    return total


def invalidate_user_cache(user_id: int = None) -> int:
    """用户数据变更后失效相关缓存"""
    total = 0
    if user_id:
        total += cache_manager.delete(CacheKey.user(user_id))
    total += cache_manager.invalidate_pattern(CacheKey.pattern_all("user"))
    total += cache_manager.invalidate_pattern(CacheKey.pattern_all("stats"))
    if total > 0:
        logger.debug("用户缓存已失效: user_id=%s, total=%d", user_id, total)
    return total


def invalidate_all_stats() -> int:
    """失效所有统计数据缓存"""
    total = cache_manager.invalidate_pattern(CacheKey.pattern_all("stats"))
    if total > 0:
        logger.debug("统计缓存已失效: total=%d", total)
    return total