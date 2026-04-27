from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ContractCreate(BaseModel):
    property_id: int
    tenant_id: int
    start_date: datetime
    end_date: datetime
    monthly_rent: float
    deposit: Optional[float] = None
    payment_day: Optional[int] = None
    terms: Optional[str] = None
    remark: Optional[str] = None


class ContractUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    monthly_rent: Optional[float] = None
    deposit: Optional[float] = None
    payment_day: Optional[int] = None
    terms: Optional[str] = None
    status: Optional[str] = None
    terminate_reason: Optional[str] = None
    remark: Optional[str] = None


class Contract(BaseModel):
    id: int
    contract_no: Optional[str] = None
    property_id: int
    landlord_id: int
    tenant_id: int
    start_date: datetime
    end_date: datetime
    monthly_rent: float
    deposit: Optional[float] = None
    payment_day: Optional[int] = None
    terms: Optional[str] = None
    status: str
    signed_by_landlord: int
    signed_by_tenant: int
    landlord_signed_at: Optional[datetime] = None
    tenant_signed_at: Optional[datetime] = None
    terminated_at: Optional[datetime] = None
    terminate_reason: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
