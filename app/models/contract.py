from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    contract_no = Column(String(50), unique=True, index=True, nullable=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    landlord_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    monthly_rent = Column(Float, nullable=False)
    deposit = Column(Float, nullable=True)
    payment_day = Column(Integer, nullable=True)
    terms = Column(Text, nullable=True)
    status = Column(String(50), default="pending_sign")
    signed_by_landlord = Column(Integer, default=0)
    signed_by_tenant = Column(Integer, default=0)
    landlord_signed_at = Column(DateTime, nullable=True)
    tenant_signed_at = Column(DateTime, nullable=True)
    terminated_at = Column(DateTime, nullable=True)
    terminate_reason = Column(String(500), nullable=True)
    remark = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property = relationship("Property", back_populates="contracts")
    landlord = relationship("User", foreign_keys=[landlord_id], back_populates="contracts_as_landlord")
    tenant = relationship("User", foreign_keys=[tenant_id], back_populates="contracts_as_tenant")
    payments = relationship("Payment", back_populates="contract")
