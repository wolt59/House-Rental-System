from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import UTCDatetimeModel


class ContractCreate(BaseModel):
    property_id: int
    tenant_id: int
    start_date: datetime
    end_date: datetime
    monthly_rent: float = Field(gt=0, description="月租金必须大于0")
    deposit: Optional[float] = Field(None, ge=0, description="押金不能为负数")
    payment_day: Optional[int] = Field(None, ge=1, le=28, description="缴费日应在1-28之间")
    terms: Optional[str] = None
    remark: Optional[str] = None

    @field_validator('end_date')
    @classmethod
    def end_date_must_be_after_start_date(cls, v, info):
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('结束日期必须晚于开始日期')
        return v


class ContractAutoCreate(BaseModel):
    property_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    deposit: Optional[float] = Field(None, ge=0, description="押金不能为负数")
    payment_day: Optional[int] = Field(None, ge=1, le=28, description="缴费日应在1-28之间")
    terms: Optional[str] = None


class ContractUpdate(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    monthly_rent: Optional[float] = Field(None, gt=0, description="月租金必须大于0")
    deposit: Optional[float] = Field(None, ge=0, description="押金不能为负数")
    payment_method: Optional[str] = Field(None, max_length=50, description="付款方式")
    payment_day: Optional[int] = Field(None, ge=1, le=31, description="缴费日应在1-31之间")
    min_lease_term: Optional[int] = Field(None, ge=1, description="最短租期（月）")
    renewal_notice_days: Optional[int] = Field(None, ge=1, le=90, description="续租提醒天数")
    check_in_time: Optional[datetime] = None
    allow_pets: Optional[int] = Field(None, ge=0, le=1, description="是否允许养宠物")
    early_termination_days: Optional[int] = Field(None, ge=1, le=90, description="提前解约通知天数")
    property_fee_bearer: Optional[str] = Field(None, max_length=50, description="物业费承担方")
    utility_fee_bearer: Optional[str] = Field(None, max_length=100, description="水电燃气费承担方")
    other_fee_bearer: Optional[str] = Field(None, max_length=200, description="其他费用承担方")
    additional_terms: Optional[str] = Field(None, max_length=2000, description="补充约定")
    terms: Optional[str] = None
    status: Optional[str] = None
    terminate_reason: Optional[str] = None
    remark: Optional[str] = None

    @field_validator('end_date')
    @classmethod
    def end_date_must_be_after_start_date(cls, v, info):
        if 'start_date' in info.data and v is not None and info.data.get('start_date') is not None:
            if v <= info.data['start_date']:
                raise ValueError('结束日期必须晚于开始日期')
        return v


class ContractReject(BaseModel):
    """拒绝合同的请求模型"""
    reason: Optional[str] = Field(None, max_length=500, description="拒绝原因")


class ContractTerminate(BaseModel):
    """终止合同的请求模型"""
    reason: Optional[str] = Field(None, max_length=500, description="终止原因")


class ContractSignRequest(BaseModel):
    """签署合同的请求模型"""
    signature_image: Optional[str] = Field(None, description="手写签名的Base64图片数据")
    ip_address: Optional[str] = Field(None, max_length=45, description="签署时的IP地址")
    device_info: Optional[str] = Field(None, max_length=200, description="签署设备信息")


class Contract(UTCDatetimeModel):
    id: int
    contract_no: Optional[str] = None
    property_id: int
    landlord_id: int
    tenant_id: int
    start_date: datetime
    end_date: datetime
    monthly_rent: float
    deposit: Optional[float] = None
    payment_method: Optional[str] = None
    payment_day: Optional[int] = None
    min_lease_term: Optional[int] = None
    renewal_notice_days: Optional[int] = None
    check_in_time: Optional[datetime] = None
    allow_pets: Optional[int] = None
    early_termination_days: Optional[int] = None
    property_fee_bearer: Optional[str] = None
    utility_fee_bearer: Optional[str] = None
    other_fee_bearer: Optional[str] = None
    additional_terms: Optional[str] = None
    terms: Optional[str] = None
    status: str
    signed_by_landlord: int
    signed_by_tenant: int
    landlord_signed_at: Optional[datetime] = None
    tenant_signed_at: Optional[datetime] = None
    landlord_sign_ip: Optional[str] = None
    landlord_sign_device: Optional[str] = None
    tenant_sign_ip: Optional[str] = None
    tenant_sign_device: Optional[str] = None
    landlord_signature_image: Optional[str] = None
    tenant_signature_image: Optional[str] = None
    terminated_at: Optional[datetime] = None
    terminate_reason: Optional[str] = None
    remark: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
