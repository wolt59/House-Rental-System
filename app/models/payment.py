from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    bill_no = Column(String(50), unique=True, index=True, nullable=True, comment="账单编号")
    payment_no = Column(String(50), unique=True, index=True, nullable=True, comment="支付单号")
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True, comment="房源ID（冗余，便于查询）")
    landlord_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="房东ID（冗余，便于查询）")
    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 账单信息
    bill_type = Column(String(50), default="rent", comment="账单类型：rent/deposit/utility/maintenance/other")
    period = Column(String(20), nullable=True, comment="所属周期，如2026-01")
    due_amount = Column(Float, nullable=False, comment="应收金额")
    actual_amount = Column(Float, nullable=True, comment="实付金额")
    
    # 支付信息
    payment_method = Column(String(50), nullable=True, comment="支付方式")
    payment_time = Column(DateTime, nullable=True, comment="付款时间")
    payment_proof = Column(String(500), nullable=True, comment="付款凭证URL")
    transaction_note = Column(String(500), nullable=True, comment="转账备注")
    
    # 状态与时间
    status = Column(String(50), default="pending", comment="账单状态")
    due_date = Column(DateTime, nullable=True, comment="付款截止日期")
    paid_at = Column(DateTime, nullable=True, comment="支付时间（旧字段保留兼容）")
    confirmed_at = Column(DateTime, nullable=True, comment="房东确认收款时间")
    
    # 逾期信息
    overdue_days = Column(Integer, default=0, comment="逾期天数")
    overdue_fee = Column(Float, default=0, comment="逾期费用")
    
    # 驳回信息
    rejected_reason = Column(String(500), nullable=True, comment="驳回原因")
    
    remark = Column(String(500), nullable=True, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    contract = relationship("Contract", back_populates="payments")
    tenant = relationship("User", foreign_keys=[tenant_id], back_populates="payments")
    landlord = relationship("User", foreign_keys=[landlord_id], back_populates="landlord_payments")
    property = relationship("Property", foreign_keys=[property_id], back_populates="payments")
