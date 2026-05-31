from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.common import UTCDatetimeModel


class ContractChangeField(BaseModel):
    """变更字段项"""
    field: str = Field(..., description="字段名")
    old_value: Optional[str] = None
    new_value: Optional[str] = None


class ContractChangeRequestCreate(BaseModel):
    """创建合同变更申请"""
    contract_id: int = Field(..., description="合同ID")
    change_reason: str = Field(..., min_length=1, max_length=2000, description="变更原因")
    change_fields: List[ContractChangeField] = Field(..., min_items=1, description="变更字段列表")


class ContractChangeRequestResponse(BaseModel):
    """响应合同变更申请"""
    approved: bool = Field(..., description="是否同意")
    response_opinion: Optional[str] = Field(None, max_length=2000, description="处理意见")


class ContractChangeRequest(UTCDatetimeModel):
    """合同变更申请完整信息"""
    id: int
    contract_id: int
    initiator_id: int
    change_reason: str
    change_fields: list  # JSON格式
    status: str
    responder_id: Optional[int] = None
    response_opinion: Optional[str] = None
    responded_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
