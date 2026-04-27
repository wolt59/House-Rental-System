from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BookingBase(BaseModel):
    property_id: int
    appointment_time: datetime
    note: Optional[str] = None


class BookingCreate(BookingBase):
    pass


class BookingInDBBase(BookingBase):
    id: int
    tenant_id: int
    status: str
    cancel_reason: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Booking(BookingInDBBase):
    pass


class BookingUpdate(BaseModel):
    appointment_time: Optional[datetime] = None
    note: Optional[str] = None
    status: Optional[str] = None
    cancel_reason: Optional[str] = None
