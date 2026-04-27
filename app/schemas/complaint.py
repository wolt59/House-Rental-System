from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ComplaintBase(BaseModel):
    property_id: int
    content: str


class ComplaintCreate(ComplaintBase):
    complaint_type: Optional[str] = None
    title: Optional[str] = None
    image_urls: Optional[str] = None


class Complaint(ComplaintBase):
    id: int
    tenant_id: int
    complaint_type: Optional[str] = None
    title: Optional[str] = None
    image_urls: Optional[str] = None
    status: str
    handled_by: Optional[str] = None
    result: Optional[str] = None
    resolved_at: Optional[datetime] = None
    remark: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComplaintUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image_urls: Optional[str] = None
    status: Optional[str] = None
    handled_by: Optional[str] = None
    result: Optional[str] = None
    remark: Optional[str] = None
