from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class ContractChangeRequest(Base):
    """合同变更申请表 - 合同生效后发起的变更申请"""
    __tablename__ = "contract_change_requests"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    initiator_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 发起人ID
    
    # 变更信息
    change_reason = Column(Text, nullable=False)  # 变更原因
    change_fields = Column(JSON, nullable=False)  # 变更字段列表，格式：[{"field": "monthly_rent", "old_value": 3000, "new_value": 3500}]
    
    # 状态管理
    status = Column(String(50), default="pending")  # pending/approved/rejected
    
    # 对方处理信息
    responder_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 响应人ID
    response_opinion = Column(Text, nullable=True)  # 对方处理意见
    responded_at = Column(DateTime, nullable=True)  # 响应时间
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    contract = relationship("Contract", back_populates="change_requests")
    initiator = relationship("User", foreign_keys=[initiator_id])
    responder = relationship("User", foreign_keys=[responder_id])
