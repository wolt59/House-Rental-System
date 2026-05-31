from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    contract_no = Column(String(50), unique=True, index=True, nullable=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    landlord_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 基础租赁信息
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    monthly_rent = Column(Float, nullable=False)
    deposit = Column(Float, nullable=True)
    payment_method = Column(String(50), nullable=True)  # 付款方式
    payment_day = Column(Integer, nullable=True)
    
    # 房屋详细信息（用于合同生成）
    min_lease_term = Column(Integer, nullable=True)  # 最短租期（月）
    renewal_notice_days = Column(Integer, nullable=True)  # 续租提醒天数
    check_in_time = Column(DateTime, nullable=True)  # 入住时间
    allow_pets = Column(Integer, default=0)  # 是否允许养宠物
    early_termination_days = Column(Integer, nullable=True)  # 解约提前天数
    
    # 费用承担方
    property_fee_bearer = Column(String(50), nullable=True)  # 物业费承担方
    utility_fee_bearer = Column(String(100), nullable=True)  # 水电燃气承担方
    other_fee_bearer = Column(String(200), nullable=True)  # 其他费用承担方
    
    # 补充约定
    additional_terms = Column(Text, nullable=True)  # 补充约定
    terms = Column(Text, nullable=True)  # 保留原有terms字段兼容
    
    # 状态管理
    status = Column(String(50), default="draft")
    
    # 签署信息
    signed_by_landlord = Column(Integer, default=0)
    signed_by_tenant = Column(Integer, default=0)
    landlord_signed_at = Column(DateTime, nullable=True)
    tenant_signed_at = Column(DateTime, nullable=True)
    
    # 签署详情记录（JSON格式存储IP、设备信息等）
    landlord_sign_ip = Column(String(45), nullable=True)
    landlord_sign_device = Column(String(200), nullable=True)
    tenant_sign_ip = Column(String(45), nullable=True)
    tenant_sign_device = Column(String(200), nullable=True)
    
    # 电子签名图片路径(Base64数据较大,使用TEXT类型)
    landlord_signature_image = Column(Text, nullable=True)
    tenant_signature_image = Column(Text, nullable=True)
    
    # 合同快照（签署后保存的HTML/PDF路径）
    contract_snapshot_html = Column(String(500), nullable=True)
    contract_snapshot_pdf = Column(String(500), nullable=True)
    
    # 终止/取消信息
    terminated_at = Column(DateTime, nullable=True)
    terminate_reason = Column(String(500), nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    cancel_reason = Column(String(500), nullable=True)
    
    remark = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property = relationship("Property", back_populates="contracts")
    landlord = relationship("User", foreign_keys=[landlord_id], back_populates="contracts_as_landlord")
    tenant = relationship("User", foreign_keys=[tenant_id], back_populates="contracts_as_tenant")
    payments = relationship("Payment", back_populates="contract")
    application = relationship("ContractApplication", back_populates="contract", uselist=False)
    change_requests = relationship("ContractChangeRequest", back_populates="contract")
    termination_requests = relationship("ContractTerminationRequest", back_populates="contract")
