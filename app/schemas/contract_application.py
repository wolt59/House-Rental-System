from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import UTCDatetimeModel


class ContractApplicationCreate(BaseModel):
    """创建合约申请"""
    booking_id: int = Field(..., description="看房记录ID")
    start_date: datetime = Field(..., description="期望租赁开始日期")
    end_date: datetime = Field(..., description="期望租赁结束日期")
    payment_method: Optional[str] = Field(None, max_length=50, description="付款方式")
    additional_notes: Optional[str] = Field(None, max_length=2000, description="补充说明")

    @field_validator('end_date')
    @classmethod
    def end_date_must_be_after_start_date(cls, v, info):
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('结束日期必须晚于开始日期')
        return v


class ContractApplicationResponse(BaseModel):
    """房东响应合约申请"""
    approved: bool = Field(..., description="是否同意")
    response: Optional[str] = Field(None, max_length=2000, description="回复/拒绝原因")


class ContractApplication(UTCDatetimeModel):
    """合约申请完整信息"""
    id: int
    booking_id: int
    property_id: int
    tenant_id: int
    landlord_id: int
    start_date: datetime
    end_date: datetime
    payment_method: Optional[str] = None
    additional_notes: Optional[str] = None
    status: str
    landlord_response: Optional[str] = None
    responded_at: Optional[datetime] = None
    contract_id: Optional[int] = None
    cancelled_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
