from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.common import UTCDatetimeModel
from app.schemas.user import User as UserSchema
from app.schemas.property import Property as PropertySchema


class BookingBase(BaseModel):
    property_id: int
    appointment_time: datetime
    note: Optional[str] = None


class BookingCreate(BookingBase):
    pass


class BookingInDBBase(BookingBase, UTCDatetimeModel):
    id: int
    tenant_id: int
    status: str
    cancel_reason: Optional[str] = None
    reject_reason: Optional[str] = None
    reschedule_proposal: Optional[str] = None
    reschedule_response: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    landlord_contact_shown: int = 0
    created_at: datetime
    updated_at: datetime
    tenant: Optional[UserSchema] = None
    property: Optional[PropertySchema] = None

    class Config:
        from_attributes = True


class Booking(BookingInDBBase):
    pass


class BookingUpdate(BaseModel):
    appointment_time: Optional[datetime] = None
    note: Optional[str] = None
    status: Optional[str] = None
    cancel_reason: Optional[str] = None
    reject_reason: Optional[str] = None
    reschedule_proposal: Optional[str] = None
    reschedule_response: Optional[str] = None
    completed_at: Optional[datetime] = None
    landlord_contact_shown: Optional[int] = None


class BookingReschedule(BaseModel):
    """房东提出改期"""
    appointment_time: datetime
    message: str


class BookingRescheduleResponse(BaseModel):
    """租客响应改期"""
    response: str  # accept, reject, cancel
    message: Optional[str] = None
