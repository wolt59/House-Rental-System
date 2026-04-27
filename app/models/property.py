from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    address = Column(String(300), nullable=False)
    region = Column(String(100), nullable=True)
    property_type = Column(String(50), nullable=True)
    floor_plan = Column(String(50), nullable=True)
    area = Column(Float, nullable=True)
    rent = Column(Float, nullable=False)
    deposit = Column(Float, nullable=True)
    decoration = Column(String(100), nullable=True)
    orientation = Column(String(50), nullable=True)
    floor_number = Column(String(20), nullable=True)
    total_floors = Column(Integer, nullable=True)
    facilities = Column(String(500), nullable=True)
    surrounding = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    view_count = Column(Integer, default=0)
    status = Column(String(50), default="vacant")
    review_status = Column(String(30), default="pending")
    review_comment = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="properties")
    bookings = relationship("Booking", back_populates="property")
    maintenance_requests = relationship("MaintenanceRequest", back_populates="property")
    complaints = relationship("Complaint", back_populates="property")
    messages = relationship("Message", back_populates="property")
    contracts = relationship("Contract", back_populates="property")
    images = relationship("PropertyImage", back_populates="property", order_by="PropertyImage.sort_order")
