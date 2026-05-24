from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.common import UTCDatetimeModel


class NewsBase(BaseModel):
    title: str
    content: str


class NewsCreate(NewsBase):
    category: Optional[str] = None
    cover_image: Optional[str] = None
    status: Optional[str] = "draft"


class NewsUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    cover_image: Optional[str] = None
    status: Optional[str] = None


class News(NewsBase, UTCDatetimeModel):
    id: int
    author_id: int
    category: Optional[str] = None
    cover_image: Optional[str] = None
    status: str
    view_count: int
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
