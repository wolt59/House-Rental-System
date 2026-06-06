"""
缓存序列化器

负责 Python 对象与 JSON 字符串之间的转换。
支持：
- Pydantic 模型
- SQLAlchemy 模型（通过 to_dict 或属性提取）
- 基本 Python 类型（dict, list, str, int, float, bool）
- 自定义编码器（datetime, Decimal 等）
"""

import json
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Optional

logger = logging.getLogger("hrs.cache")


class CacheEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，支持 datetime、Decimal 等类型"""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if hasattr(obj, "__dict__"):
            # SQLAlchemy 模型尝试转为 dict
            return self._model_to_dict(obj)
        return super().default(obj)

    @staticmethod
    def _model_to_dict(obj: Any) -> dict:
        """将 SQLAlchemy 模型转为字典"""
        result = {}
        for key in dir(obj):
            if key.startswith("_"):
                continue
            value = getattr(obj, key, None)
            if callable(value):
                continue
            if isinstance(value, (datetime, date)):
                result[key] = value.isoformat()
            elif isinstance(value, Decimal):
                result[key] = float(value)
            elif isinstance(value, (str, int, float, bool, type(None))):
                result[key] = value
            elif isinstance(value, (list, dict)):
                result[key] = value
        return result


def serialize(data: Any) -> Optional[str]:
    """
    序列化数据为 JSON 字符串。

    参数:
        data: 要序列化的 Python 对象

    返回:
        JSON 字符串，失败返回 None
    """
    if data is None:
        return None
    try:
        return json.dumps(data, cls=CacheEncoder, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        logger.error("缓存序列化失败: %s", e)
        return None


def deserialize(data: Optional[str]) -> Any:
    """
    反序列化 JSON 字符串为 Python 对象。

    参数:
        data: JSON 字符串

    返回:
        反序列化后的 Python 对象，失败返回 None
    """
    if data is None:
        return None
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError) as e:
        logger.error("缓存反序列化失败: %s", e)
        return None