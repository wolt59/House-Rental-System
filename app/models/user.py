from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    phone = Column(String(30), unique=True, index=True, nullable=True)
    full_name = Column(String(120), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="tenant")
    is_active = Column(Boolean, default=True)
    id_card_number = Column(String(30), nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)
    remark = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    properties = relationship("Property", back_populates="owner")
    bookings = relationship("Booking", back_populates="tenant")
    maintenance_requests = relationship("MaintenanceRequest", back_populates="tenant")
    complaints = relationship("Complaint", back_populates="tenant")
    messages_sent = relationship("Message", foreign_keys="Message.from_user_id", back_populates="from_user")
    messages_received = relationship("Message", foreign_keys="Message.to_user_id", back_populates="to_user")
    contracts_as_landlord = relationship("Contract", foreign_keys="Contract.landlord_id", back_populates="landlord")
    contracts_as_tenant = relationship("Contract", foreign_keys="Contract.tenant_id", back_populates="tenant")
    payments = relationship("Payment", foreign_keys="Payment.tenant_id", back_populates="tenant")
