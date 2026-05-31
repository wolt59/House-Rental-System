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
    city = Column(String(50), nullable=True)  # 所属城市
    community_name = Column(String(200), nullable=True)  # 小区名称
    property_type = Column(String(50), nullable=True)
    rental_type = Column(String(50), nullable=True)  # 房源类型（整租/合租/公寓/商铺）
    floor_plan = Column(String(50), nullable=True)
    bedrooms = Column(Integer, nullable=True)  # 卧室数量
    livingrooms = Column(Integer, nullable=True)  # 客厅数量
    bathrooms = Column(Integer, nullable=True)  # 卫生间数量
    area = Column(Float, nullable=True)
    building_area = Column(Float, nullable=True)  # 建筑面积
    usable_area = Column(Float, nullable=True)  # 实用面积
    rent = Column(Float, nullable=False)
    deposit = Column(Float, nullable=True)
    payment_method = Column(String(50), nullable=True)  # 付款方式
    decoration = Column(String(100), nullable=True)
    orientation = Column(String(50), nullable=True)
    floor_number = Column(String(20), nullable=True)
    total_floors = Column(Integer, nullable=True)
    min_lease_term = Column(Integer, nullable=True)  # 最短租期（月）
    earliest_move_in_date = Column(String(50), nullable=True)  # 最早可入住时间
    property_fee_bearer = Column(String(50), nullable=True)  # 物业费承担方
    utility_fee_bearer = Column(String(100), nullable=True)  # 水电燃气费承担方
    other_fee_bearer = Column(String(200), nullable=True)  # 其他费用承担方
    allow_pets = Column(Integer, default=0)  # 是否允许宠物（0=否，1=是）
    build_year = Column(Integer, nullable=True)  # 建筑年代
    has_elevator = Column(Integer, nullable=True)  # 电梯配置
    total_households = Column(Integer, nullable=True)  # 总户数
    property_management_type = Column(String(100), nullable=True)  # 物业类型
    facilities = Column(String(500), nullable=True)
    surrounding = Column(Text, nullable=True)
    viewing_time_rules = Column(String(500), nullable=True)  # 看房时间规则
    video_url = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    view_count = Column(Integer, default=0)
    status = Column(String(50), default="unpublished")  # published/unpublished/vacant/rented/maintenance
    review_status = Column(String(30), default="draft")  # draft/pending/reviewing/approved/rejected
    review_comment = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(String(500), nullable=True)  # 特色标签
    landlord_notes = Column(Text, nullable=True)  # 房东备注
    submitted_at = Column(DateTime, nullable=True)  # 提交审核时间
    approved_at = Column(DateTime, nullable=True)  # 审核通过时间
    published_at = Column(DateTime, nullable=True)  # 发布时间
    unpublished_at = Column(DateTime, nullable=True)  # 暂停发布时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="properties")
    bookings = relationship("Booking", back_populates="property")
    maintenance_requests = relationship("MaintenanceRequest", back_populates="property")
    complaints = relationship("Complaint", back_populates="property")
    messages = relationship("Message", back_populates="property")
    contracts = relationship("Contract", back_populates="property")
    contract_applications = relationship("ContractApplication", back_populates="property")
    images = relationship("PropertyImage", back_populates="property", order_by="PropertyImage.sort_order")
