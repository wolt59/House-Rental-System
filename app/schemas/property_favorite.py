from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import UTCDatetimeModel


# ============== 收藏 ==============

class PropertyFavoriteCreate(BaseModel):
    """切换收藏：传入 property_id 即可，若已收藏则取消，若未收藏则新增"""
    property_id: int


class PropertyFavorite(UTCDatetimeModel):
    id: int
    property_id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PropertyFavoriteWithProperty(PropertyFavorite):
    """收藏列表项：附带房源摘要信息（用于"我的收藏"页面）"""
    property_title: Optional[str] = None
    property_address: Optional[str] = None
    property_rent: Optional[float] = None
    property_status: Optional[str] = None
    property_cover: Optional[str] = None


class PropertyFavoriteToggleResponse(BaseModel):
    """收藏切换结果"""
    property_id: int
    is_favorited: bool
    favorite_count: int


# ============== 评论 ==============

class PropertyCommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)


class PropertyCommentCreate(PropertyCommentBase):
    property_id: int


class PropertyCommentUpdate(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)


class PropertyComment(PropertyCommentBase, UTCDatetimeModel):
    id: int
    property_id: int
    user_id: int
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    user_role: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_validator("content", mode="before")
    @classmethod
    def strip_content(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    class Config:
        from_attributes = True
