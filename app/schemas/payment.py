from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import UTCDatetimeModel


class PaymentCreate(BaseModel):
    """系统生成账单"""
    contract_id: int
    bill_type: str = "rent"
    period: Optional[str] = None
    due_amount: float = Field(..., gt=0, description="应收金额")
    due_date: Optional[datetime] = None
    remark: Optional[str] = None
    property_id: Optional[int] = None
    landlord_id: Optional[int] = None


class PaymentSubmit(BaseModel):
    """租客提交付款"""
    actual_amount: Optional[float] = Field(None, gt=0, description="实付金额")
    payment_method: Optional[str] = None
    payment_time: Optional[datetime] = None
    transaction_note: Optional[str] = None
    payment_proof: Optional[str] = None


class PaymentReject(BaseModel):
    """房东驳回付款"""
    rejected_reason: str = Field(..., min_length=1, description="驳回原因")


class PaymentConfirm(BaseModel):
    """房东确认收款（无需额外字段）"""
    pass


class PaymentUpdate(BaseModel):
    """管理员更新账单"""
    status: Optional[str] = None
    due_amount: Optional[float] = None
    due_date: Optional[datetime] = None
    overdue_days: Optional[int] = None
    overdue_fee: Optional[float] = None
    remark: Optional[str] = None


class Payment(UTCDatetimeModel):
    id: int
    bill_no: Optional[str] = None
    payment_no: Optional[str] = None
    contract_id: int
    property_id: Optional[int] = None
    landlord_id: Optional[int] = None
    tenant_id: int
    bill_type: str
    period: Optional[str] = None
    due_amount: float
    actual_amount: Optional[float] = None
    payment_method: Optional[str] = None
    payment_time: Optional[datetime] = None
    payment_proof: Optional[str] = None
    transaction_note: Optional[str] = None
    status: str
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    overdue_days: int
    overdue_fee: float
    rejected_reason: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentWithDetails(Payment):
    """带关联信息的账单"""
    tenant_name: Optional[str] = None
    landlord_name: Optional[str] = None
    property_title: Optional[str] = None
    contract_no: Optional[str] = None
