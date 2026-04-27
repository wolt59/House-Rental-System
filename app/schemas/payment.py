from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PaymentCreate(BaseModel):
    contract_id: int
    amount: float
    payment_method: Optional[str] = None
    due_date: Optional[datetime] = None
    remark: Optional[str] = None


class PaymentUpdate(BaseModel):
    status: Optional[str] = None
    payment_method: Optional[str] = None
    overdue_days: Optional[int] = None
    overdue_fee: Optional[float] = None
    remark: Optional[str] = None


class Payment(BaseModel):
    id: int
    payment_no: Optional[str] = None
    contract_id: int
    tenant_id: int
    amount: float
    payment_method: Optional[str] = None
    status: str
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    overdue_days: int
    overdue_fee: float
    remark: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
