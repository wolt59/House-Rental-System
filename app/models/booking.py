from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base import Base


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    appointment_time = Column(DateTime, nullable=False)
    status = Column(String(50), default="pending")
    cancel_reason = Column(String(500), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    note = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("User", back_populates="bookings")
    property = relationship("Property", back_populates="bookings")
