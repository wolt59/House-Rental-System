from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MaintenanceBase(BaseModel):
    property_id: int
    description: str


class MaintenanceCreate(MaintenanceBase):
    title: Optional[str] = None
    image_urls: Optional[str] = None
    priority: Optional[str] = "normal"


class Maintenance(MaintenanceBase):
    id: int
    tenant_id: int
    title: Optional[str] = None
    image_urls: Optional[str] = None
    priority: str
    status: str
    assigned_to: Optional[str] = None
    completed_at: Optional[datetime] = None
    feedback: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MaintenanceUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    image_urls: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    feedback: Optional[str] = None
    remark: Optional[str] = None
