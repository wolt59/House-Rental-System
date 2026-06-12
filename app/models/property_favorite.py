from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from app.db.base import Base


class PropertyFavorite(Base):
    """房源收藏：用户（任意角色）可收藏/取消收藏房源"""
    __tablename__ = "property_favorites"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    property = relationship("Property", back_populates="favorites")
    user = relationship("User", back_populates="favorites")

    __table_args__ = (
        UniqueConstraint("property_id", "user_id", name="uq_property_favorite_property_user"),
        Index("ix_property_favorite_user", "user_id"),
        Index("ix_property_favorite_property", "property_id"),
    )


class PropertyComment(Base):
    """房源评论：用户（任意角色）可对房源发表评论"""
    __tablename__ = "property_comments"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    property = relationship("Property", back_populates="comments")
    user = relationship("User", back_populates="comments")

    __table_args__ = (
        Index("ix_property_comment_property", "property_id"),
        Index("ix_property_comment_user", "user_id"),
    )
