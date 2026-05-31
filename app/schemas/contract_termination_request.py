from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.common import UTCDatetimeModel


class ContractTerminationRequestCreate(BaseModel):
    """创建提前解约申请"""
    contract_id: int = Field(..., description="合同ID")
    termination_reason: str = Field(..., min_length=1, max_length=2000, description="解约原因")
    expected_termination_date: datetime = Field(..., description="期望解约日期")
    penalty_amount: Optional[float] = Field(None, ge=0, description="违约金金额")
    deposit_handling: Optional[str] = Field(None, max_length=1000, description="押金处理说明")
    additional_notes: Optional[str] = Field(None, max_length=2000, description="备注")


class ContractTerminationRequest(UTCDatetimeModel):
    """提前解约申请完整信息"""
    id: int
    contract_id: int
    initiator_id: int
    termination_reason: str
    expected_termination_date: datetime
    penalty_amount: Optional[float] = None
    deposit_handling: Optional[str] = None
    additional_notes: Optional[str] = None
    status: str
    responder_id: Optional[int] = None
    response_opinion: Optional[str] = None
    responded_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
