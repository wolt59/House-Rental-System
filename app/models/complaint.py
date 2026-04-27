from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    complaint_type = Column(String(50), nullable=True)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    image_urls = Column(String(1000), nullable=True)
    status = Column(String(50), default="open")
    handled_by = Column(String(120), nullable=True)
    result = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    remark = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property = relationship("Property", back_populates="complaints")
    tenant = relationship("User", back_populates="complaints")
