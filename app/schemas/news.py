from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import UTCDatetimeModel


class NewsBase(BaseModel):
    title: str
    content: str


class NewsCreate(NewsBase):
    category: Optional[str] = None
    cover_image: Optional[str] = None
    status: Optional[str] = "draft"  # draft=存草稿, published=立即发布


class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    cover_image: Optional[str] = None
    status: Optional[str] = None  # draft | published


class NewsReview(BaseModel):
    """管理员审核操作（先发布后审核）"""
    action: str = Field(..., description="approve=恢复发布, reject=下架")
    message: Optional[str] = Field(None, description="审核意见（下架时必填）")


class News(NewsBase, UTCDatetimeModel):
    id: int
    author_id: int
    category: Optional[str] = None
    cover_image: Optional[str] = None
    status: str
    review_message: Optional[str] = None
    view_count: int
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    author_name: Optional[str] = None

    class Config:
        from_attributes = True
