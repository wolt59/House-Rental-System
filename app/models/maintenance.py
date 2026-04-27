from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=False)
    image_urls = Column(String(1000), nullable=True)
    priority = Column(String(20), default="normal")
    status = Column(String(50), default="new")
    assigned_to = Column(String(120), nullable=True)
    completed_at = Column(DateTime, nullable=True)
    feedback = Column(String(500), nullable=True)
    remark = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property = relationship("Property", back_populates="maintenance_requests")
    tenant = relationship("User", back_populates="maintenance_requests")
