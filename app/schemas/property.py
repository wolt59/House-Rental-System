from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, constr


class PropertyImageBase(BaseModel):
    image_url: str
    image_type: Optional[str] = "photo"
    is_cover: Optional[int] = 0
    sort_order: Optional[int] = 0


class PropertyImage(PropertyImageBase):
    id: int
    property_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PropertyBase(BaseModel):
    title: constr(min_length=3, max_length=200)
    address: constr(min_length=3, max_length=300)
    region: Optional[str] = None
    property_type: Optional[str] = None
    floor_plan: Optional[str] = None
    area: Optional[float] = None
    rent: float
    deposit: Optional[float] = None
    decoration: Optional[str] = None
    orientation: Optional[str] = None
    floor_number: Optional[str] = None
    total_floors: Optional[int] = None
    facilities: Optional[str] = None
    surrounding: Optional[str] = None
    video_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: Optional[str] = "vacant"
    review_status: Optional[str] = "pending"
    description: Optional[str] = None


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    title: Optional[constr(min_length=3, max_length=200)] = None
    address: Optional[constr(min_length=3, max_length=300)] = None
    region: Optional[str] = None
    property_type: Optional[str] = None
    floor_plan: Optional[str] = None
    area: Optional[float] = None
    rent: Optional[float] = None
    deposit: Optional[float] = None
    decoration: Optional[str] = None
    orientation: Optional[str] = None
    floor_number: Optional[str] = None
    total_floors: Optional[int] = None
    facilities: Optional[str] = None
    surrounding: Optional[str] = None
    video_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: Optional[str] = None
    review_status: Optional[str] = None
    description: Optional[str] = None


class PropertyInDBBase(PropertyBase):
    id: int
    owner_id: int
    view_count: int
    review_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    images: Optional[List[PropertyImage]] = []

    class Config:
        from_attributes = True


class Property(PropertyInDBBase):
    pass


class PropertyReview(BaseModel):
    review_status: str
    comment: Optional[str] = None


class PropertyStatusUpdate(BaseModel):
    status: str


class RegionStats(BaseModel):
    region: str
    property_count: int

    class Config:
        from_attributes = True


class FloorPlanStats(BaseModel):
    floor_plan: str
    property_count: int

    class Config:
        from_attributes = True
