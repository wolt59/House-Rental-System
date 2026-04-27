from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_no = Column(String(50), unique=True, index=True, nullable=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=True)
    status = Column(String(50), default="pending")
    due_date = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    overdue_days = Column(Integer, default=0)
    overdue_fee = Column(Float, default=0)
    remark = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contract = relationship("Contract", back_populates="payments")
    tenant = relationship("User", back_populates="payments")
