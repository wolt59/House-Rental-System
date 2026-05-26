from typing import List, Optional
from datetime import datetime
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.user import User
from app.schemas.property import PropertyCreate, PropertyUpdate


def get_property(db: Session, property_id: int) -> Optional[Property]:
    return db.query(Property).filter(Property.id == property_id).first()


def get_properties(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    region: str | None = None,
    floor_plan: str | None = None,
    owner_id: int | None = None,
    review_status: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
):
    query = db.query(Property)
    if owner_id is not None:
        query = query.filter(Property.owner_id == owner_id)
    if region:
        query = query.filter(Property.region == region)
    if floor_plan:
        query = query.filter(Property.floor_plan == floor_plan)
    if review_status is not None:
        query = query.filter(Property.review_status == review_status)
    if status is not None:
        query = query.filter(Property.status == status)
    if keyword:
        from sqlalchemy import or_
        query = query.filter(
            or_(
                Property.title.contains(keyword),
                Property.address.contains(keyword),
            )
        )
    return query.offset(skip).limit(limit).all()


def create_property(db: Session, owner_id: int, property_in: PropertyCreate) -> Property:
    data = property_in.dict()
    data["owner_id"] = owner_id
    data["review_status"] = "draft"  # 创建后为草稿状态
    if not data.get("status"):
        data["status"] = "unpublished"  # 默认为未发布状态
    property_obj = Property(**data)
    db.add(property_obj)
    db.commit()
    db.refresh(property_obj)
    return property_obj


def update_property(db: Session, db_property: Property, property_in: PropertyUpdate) -> Property:
    for field, value in property_in.dict(exclude_unset=True).items():
        setattr(db_property, field, value)
    db.commit()
    db.refresh(db_property)
    return db_property


def remove_property(db: Session, db_property: Property) -> Property:
    db.delete(db_property)
    db.commit()
    return db_property


def submit_for_review(db: Session, db_property: Property) -> Property:
    """提交审核（房东操作）"""
    if db_property.review_status not in ["draft", "rejected"]:
        raise ValueError(f"当前状态({db_property.review_status})不允许提交审核")
    
    db_property.review_status = "pending"
    db_property.submitted_at = datetime.utcnow()
    db.commit()
    db.refresh(db_property)
    return db_property


def start_review(db: Session, db_property: Property) -> Property:
    """开始审核（管理员操作）"""
    if db_property.review_status != "pending":
        raise ValueError(f"当前状态({db_property.review_status})不允许开始审核")
    
    db_property.review_status = "reviewing"
    db.commit()
    db.refresh(db_property)
    return db_property


def approve_property(db: Session, db_property: Property, comment: Optional[str] = None) -> Property:
    """审核通过（管理员操作）"""
    if db_property.review_status != "reviewing":
        raise ValueError(f"当前状态({db_property.review_status})不允许审核")
    
    db_property.review_status = "approved"
    db_property.status = "published"  # 审核通过后自动发布
    db_property.approved_at = datetime.utcnow()
    db_property.published_at = datetime.utcnow()
    if comment:
        db_property.review_comment = comment
    db.commit()
    db.refresh(db_property)
    return db_property


def reject_property(db: Session, db_property: Property, comment: str) -> Property:
    """审核拒绝（管理员操作）"""
    if db_property.review_status != "reviewing":
        raise ValueError(f"当前状态({db_property.review_status})不允许审核")
    
    db_property.review_status = "rejected"
    db_property.review_comment = comment
    db.commit()
    db.refresh(db_property)
    return db_property


def unpublish_property(db: Session, db_property: Property) -> Property:
    """暂停发布（房东操作）"""
    if db_property.review_status != "approved":
        raise ValueError("只有审核通过的房源才能暂停发布")
    if db_property.status in ["rented", "maintenance"]:
        raise ValueError(f"当前房源状态({db_property.status})不允许暂停发布")
    
    db_property.status = "unpublished"
    db_property.unpublished_at = datetime.utcnow()
    db.commit()
    db.refresh(db_property)
    return db_property


def republish_property(db: Session, db_property: Property) -> Property:
    """重新发布（房东操作）"""
    if db_property.review_status != "approved":
        raise ValueError("只有审核通过的房源才能重新发布")
    if db_property.status != "unpublished":
        raise ValueError(f"当前房源状态({db_property.status})不是暂停发布状态")
    
    db_property.status = "published"
    db_property.published_at = datetime.utcnow()
    db_property.unpublished_at = None
    db.commit()
    db.refresh(db_property)
    return db_property


def admin_unpublish_property(db: Session, db_property: Property, reason: Optional[str] = None) -> Property:
    """管理员强制下架（变为草稿和未发布状态，房东可修改后重新提交）"""
    if db_property.status in ["rented", "maintenance"]:
        raise ValueError(f"当前房源状态({db_property.status})不允许下架")
    
    db_property.status = "unpublished"  # 未发布
    db_property.review_status = "draft"  # 草稿状态，房东可以修改后重新提交
    db_property.unpublished_at = datetime.utcnow()
    if reason:
        db_property.review_comment = f"管理员下架：{reason}"
    db.commit()
    db.refresh(db_property)
    return db_property


def get_landlord_property_stats(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    owner_id: Optional[int] = None,
):
    query = (
        db.query(
            User.id.label("owner_id"),
            User.username,
            User.email,
            User.full_name,
            func.coalesce(func.count(Property.id), 0).label("total_properties"),
            func.coalesce(
                func.sum(case((Property.review_status == "approved", 1), else_=0)), 0
            ).label("approved_properties"),
            func.coalesce(
                func.sum(case((Property.review_status == "pending", 1), else_=0)), 0
            ).label("pending_properties"),
            func.coalesce(
                func.sum(case((Property.review_status == "rejected", 1), else_=0)), 0
            ).label("rejected_properties"),
            func.coalesce(
                func.sum(case((Property.status == "vacant", 1), else_=0)), 0
            ).label("vacant_properties"),
            func.coalesce(
                func.sum(case((Property.status == "rented", 1), else_=0)), 0
            ).label("rented_properties"),
            func.coalesce(
                func.sum(case((Property.status == "maintenance", 1), else_=0)), 0
            ).label("maintenance_properties"),
        )
        .outerjoin(Property, Property.owner_id == User.id)
        .filter(User.role == "landlord")
    )
    if owner_id is not None:
        query = query.filter(User.id == owner_id)
    results = (
        query.group_by(User.id, User.username, User.email, User.full_name)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "owner_id": row.owner_id,
            "username": row.username,
            "email": row.email,
            "full_name": row.full_name,
            "total_properties": row.total_properties,
            "approved_properties": row.approved_properties,
            "pending_properties": row.pending_properties,
            "rejected_properties": row.rejected_properties,
            "vacant_properties": row.vacant_properties,
            "rented_properties": row.rented_properties,
            "maintenance_properties": row.maintenance_properties,
        }
        for row in results
    ]
