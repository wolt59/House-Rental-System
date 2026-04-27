from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)
    message_type = Column(String(30), default="text")
    content = Column(String(1000), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="messages_sent")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="messages_received")
    property = relationship("Property", back_populates="messages")
