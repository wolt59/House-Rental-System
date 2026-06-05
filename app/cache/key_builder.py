"""
缓存键管理

提供统一的缓存键生成规则，确保：
- 命名空间隔离（通过 key_prefix）
- 可读性（层级结构）
- 一致性（统一的命名规范）
- 可扩展性（支持分布式缓存的 hash tag 预留）
"""

from app.core.config import settings


class CacheKey:
    """
    缓存键构造器

    命名规范: {prefix}:{entity}:{identifier}

    示例:
        key = CacheKey.property(property_id=123)
        # => "hrs:property:123"

        key = CacheKey.property_list(region="北京", page=1)
        # => "hrs:property:list:region=北京:page=1"
    """

    _prefix = settings.CACHE_KEY_PREFIX

    @classmethod
    def _build(cls, *parts: str) -> str:
        return ":".join(filter(None, [cls._prefix, *parts]))

    # ========== Property 房源 ==========

    @classmethod
    def property(cls, property_id: int) -> str:
        return cls._build("property", str(property_id))

    @classmethod
    def property_list(cls, **filters) -> str:
        params = ":".join(f"{k}={v}" for k, v in sorted(filters.items()) if v is not None)
        return cls._build("property", "list", params) if params else cls._build("property", "list")

    # ========== User 用户 ==========

    @classmethod
    def user(cls, user_id: int) -> str:
        return cls._build("user", str(user_id))

    @classmethod
    def user_list(cls, **filters) -> str:
        params = ":".join(f"{k}={v}" for k, v in sorted(filters.items()) if v is not None)
        return cls._build("user", "list", params) if params else cls._build("user", "list")

    # ========== Booking 预约 ==========

    @classmethod
    def booking(cls, booking_id: int) -> str:
        return cls._build("booking", str(booking_id))

    @classmethod
    def booking_list(cls, **filters) -> str:
        params = ":".join(f"{k}={v}" for k, v in sorted(filters.items()) if v is not None)
        return cls._build("booking", "list", params) if params else cls._build("booking", "list")

    # ========== Contract 合同 ==========

    @classmethod
    def contract(cls, contract_id: int) -> str:
        return cls._build("contract", str(contract_id))

    @classmethod
    def contract_list(cls, **filters) -> str:
        params = ":".join(f"{k}={v}" for k, v in sorted(filters.items()) if v is not None)
        return cls._build("contract", "list", params) if params else cls._build("contract", "list")

    # ========== News 新闻 ==========

    @classmethod
    def news(cls, news_id: int) -> str:
        return cls._build("news", str(news_id))

    @classmethod
    def news_list(cls, **filters) -> str:
        params = ":".join(f"{k}={v}" for k, v in sorted(filters.items()) if v is not None)
        return cls._build("news", "list", params) if params else cls._build("news", "list")

    # ========== Stats 统计 ==========

    @classmethod
    def stats(cls, name: str) -> str:
        return cls._build("stats", name)

    @classmethod
    def dashboard_stats(cls) -> str:
        return cls._build("stats", "dashboard")

    # ========== 通配符模式（用于批量失效） ==========

    @classmethod
    def pattern_all(cls, entity: str) -> str:
        """获取某个实体的所有缓存键模式"""
        return cls._build(entity, "*")

    @classmethod
    def pattern_list(cls, entity: str) -> str:
        """获取某个实体的列表缓存键模式"""
        return cls._build(entity, "list", "*")