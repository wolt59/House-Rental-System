from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class ContractApplication(Base):
    """合约申请表 - 租客在看房完成后发起的租赁申请"""
    __tablename__ = "contract_applications"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)  # 关联的看房记录
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)  # 房源ID
    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 租客ID
    landlord_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 房东ID
    
    # 租客填写的期望租赁信息
    start_date = Column(DateTime, nullable=False)  # 期望租赁开始日期
    end_date = Column(DateTime, nullable=False)  # 期望租赁结束日期
    payment_method = Column(String(50), nullable=True)  # 付款方式（如：押一付三）
    additional_notes = Column(Text, nullable=True)  # 补充说明
    
    # 状态管理
    status = Column(String(50), default="apply_pending")  # APPLY_PENDING/APPLY_APPROVED/APPLY_REJECTED/APPLY_CANCELLED
    
    # 房东处理信息
    landlord_response = Column(Text, nullable=True)  # 房东回复/拒绝原因
    responded_at = Column(DateTime, nullable=True)  # 房东响应时间
    
    # 关联的合同ID（房东同意后生成）
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)  # 取消时间
    
    # 关系
    booking = relationship("Booking", back_populates="contract_applications")
    property = relationship("Property", back_populates="contract_applications")
    tenant = relationship("User", foreign_keys=[tenant_id], back_populates="contract_applications_as_tenant")
    landlord = relationship("User", foreign_keys=[landlord_id], back_populates="contract_applications_as_landlord")
    contract = relationship("Contract", back_populates="application")
