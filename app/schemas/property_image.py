from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PropertyImageCreate(BaseModel):
    image_url: str
    image_type: Optional[str] = "photo"
    is_cover: Optional[int] = 0
    sort_order: Optional[int] = 0


class PropertyImageUpdate(BaseModel):
    image_type: Optional[str] = None
    is_cover: Optional[int] = None
    sort_order: Optional[int] = None


class PropertyImage(BaseModel):
    id: int
    property_id: int
    image_url: str
    image_type: str
    is_cover: int
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True
