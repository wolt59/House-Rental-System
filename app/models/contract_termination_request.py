from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class ContractTerminationRequest(Base):
    """合同提前解约申请表 - 合同生效后发起的提前解约申请"""
    __tablename__ = "contract_termination_requests"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    initiator_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 发起人ID
    
    # 解约信息
    termination_reason = Column(Text, nullable=False)  # 解约原因
    expected_termination_date = Column(DateTime, nullable=False)  # 期望解约日期
    penalty_amount = Column(Float, nullable=True)  # 违约金金额
    deposit_handling = Column(Text, nullable=True)  # 押金处理说明
    additional_notes = Column(Text, nullable=True)  # 备注
    
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
    contract = relationship("Contract", back_populates="termination_requests")
    initiator = relationship("User", foreign_keys=[initiator_id])
    responder = relationship("User", foreign_keys=[responder_id])
