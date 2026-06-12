from typing import List, Optional
from datetime import datetime
from sqlalchemy import case, desc, func, or_
from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.user import User
from app.schemas.property import PropertyCreate
from app.core.enums import PropertyReviewStatus, PropertyStatus

# 最大图片数量限制
MAX_PROPERTY_IMAGES = 9
# 描述最大长度
MAX_DESCRIPTION_LENGTH = 2000


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
    rent_min: float | None = None,
    rent_max: float | None = None,
    property_type: str | None = None,
    rental_type: str | None = None,
    decoration: str | None = None,
    bedrooms: int | None = None,
    sort_by: str | None = None,
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
        query = query.filter(
            or_(
                Property.title.contains(keyword),
                Property.address.contains(keyword),
                Property.community_name.contains(keyword),
                Property.description.contains(keyword),
                Property.tags.contains(keyword),
                Property.region.contains(keyword),
            )
        )
    if rent_min is not None:
        query = query.filter(Property.rent >= rent_min)
    if rent_max is not None:
        query = query.filter(Property.rent <= rent_max)
    if property_type:
        query = query.filter(Property.property_type == property_type)
    if rental_type:
        query = query.filter(Property.rental_type == rental_type)
    if decoration:
        query = query.filter(Property.decoration == decoration)
    if bedrooms is not None:
        query = query.filter(Property.bedrooms == bedrooms)
    
    # 排序
    if sort_by == "price_asc":
        query = query.order_by(Property.rent.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Property.rent.desc())
    elif sort_by == "newest":
        query = query.order_by(desc(Property.published_at), desc(Property.created_at))
    elif sort_by == "oldest":
        query = query.order_by(Property.published_at.asc(), Property.created_at.asc())
    elif sort_by == "views":
        query = query.order_by(desc(Property.view_count))
    else:
        # 默认综合排序：按发布时间倒序
        query = query.order_by(desc(Property.published_at), desc(Property.created_at))
    
    return query.offset(skip).limit(limit).all()


def count_properties(
    db: Session,
    region: str | None = None,
    floor_plan: str | None = None,
    owner_id: int | None = None,
    review_status: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    rent_min: float | None = None,
    rent_max: float | None = None,
    property_type: str | None = None,
    rental_type: str | None = None,
    decoration: str | None = None,
    bedrooms: int | None = None,
) -> int:
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
        query = query.filter(
            or_(
                Property.title.contains(keyword),
                Property.address.contains(keyword),
                Property.community_name.contains(keyword),
                Property.description.contains(keyword),
                Property.tags.contains(keyword),
                Property.region.contains(keyword),
            )
        )
    if rent_min is not None:
        query = query.filter(Property.rent >= rent_min)
    if rent_max is not None:
        query = query.filter(Property.rent <= rent_max)
    if property_type:
        query = query.filter(Property.property_type == property_type)
    if rental_type:
        query = query.filter(Property.rental_type == rental_type)
    if decoration:
        query = query.filter(Property.decoration == decoration)
    if bedrooms is not None:
        query = query.filter(Property.bedrooms == bedrooms)
    return query.count()


def create_property(db: Session, owner_id: int, property_in: PropertyCreate) -> Property:
    data = property_in.model_dump()
    data["owner_id"] = owner_id
    data["review_status"] = PropertyReviewStatus.DRAFT.value
    if not data.get("status"):
        data["status"] = PropertyStatus.UNPUBLISHED.value
    property_obj = Property(**data)
    db.add(property_obj)
    db.commit()
    db.refresh(property_obj)
    return property_obj


def remove_property(db: Session, db_property: Property) -> Property:
    db.delete(db_property)
    db.commit()
    return db_property


def submit_for_review(db: Session, db_property: Property) -> Property:
    """提交审核（房东操作）"""
    if db_property.review_status not in [PropertyReviewStatus.DRAFT.value, PropertyReviewStatus.REJECTED.value]:
        raise ValueError(f"当前状态({db_property.review_status})不允许提交审核")
    
    db_property.review_status = PropertyReviewStatus.PENDING.value
    db_property.submitted_at = datetime.utcnow()
    db.commit()
    db.refresh(db_property)
    return db_property


def start_review(db: Session, db_property: Property) -> Property:
    """开始审核（管理员操作）"""
    if db_property.review_status != PropertyReviewStatus.PENDING.value:
        raise ValueError(f"当前状态({db_property.review_status})不允许开始审核")
    
    db_property.review_status = PropertyReviewStatus.REVIEWING.value
    db.commit()
    db.refresh(db_property)
    return db_property


def approve_property(db: Session, db_property: Property, comment: Optional[str] = None) -> Property:
    """审核通过（管理员操作）"""
    if db_property.review_status != PropertyReviewStatus.REVIEWING.value:
        raise ValueError(f"当前状态({db_property.review_status})不允许审核")
    
    db_property.review_status = PropertyReviewStatus.APPROVED.value
    db_property.status = PropertyStatus.PUBLISHED.value
    db_property.approved_at = datetime.utcnow()
    db_property.published_at = datetime.utcnow()
    if comment:
        db_property.review_comment = comment
    db.commit()
    db.refresh(db_property)
    return db_property


def reject_property(db: Session, db_property: Property, comment: str) -> Property:
    """审核拒绝（管理员操作）"""
    if db_property.review_status != PropertyReviewStatus.REVIEWING.value:
        raise ValueError(f"当前状态({db_property.review_status})不允许审核")
    
    db_property.review_status = PropertyReviewStatus.REJECTED.value
    db_property.review_comment = comment
    db.commit()
    db.refresh(db_property)
    return db_property


def unpublish_property(db: Session, db_property: Property) -> Property:
    """暂停发布（房东操作）"""
    if db_property.review_status != PropertyReviewStatus.APPROVED.value:
        raise ValueError("只有审核通过的房源才能暂停发布")
    if db_property.status == PropertyStatus.RENTED.value:
        raise ValueError(f"当前房源状态({db_property.status})不允许暂停发布")
    
    db_property.status = PropertyStatus.UNPUBLISHED.value
    db_property.unpublished_at = datetime.utcnow()
    db.commit()
    db.refresh(db_property)
    return db_property


def republish_property(db: Session, db_property: Property) -> Property:
    """重新发布"""
    if db_property.review_status != PropertyReviewStatus.APPROVED.value:
        raise ValueError("只有审核通过的房源才能重新发布")
    if db_property.status != PropertyStatus.UNPUBLISHED.value:
        raise ValueError(f"当前房源状态({db_property.status})不是暂停发布状态")
    
    db_property.status = PropertyStatus.PUBLISHED.value
    db_property.published_at = datetime.utcnow()
    db_property.unpublished_at = None
    db.commit()
    db.refresh(db_property)
    return db_property


def withdraw_review(db: Session, db_property: Property) -> Property:
    """撤销审核申请（房东操作：在未审核通过前可撤回，变回草稿状态）"""
    if db_property.review_status not in [PropertyReviewStatus.PENDING.value, PropertyReviewStatus.REVIEWING.value]:
        raise ValueError(f"当前状态({db_property.review_status})不允许撤销审核")
    
    db_property.review_status = PropertyReviewStatus.DRAFT.value
    db_property.status = PropertyStatus.UNPUBLISHED.value
    db_property.submitted_at = None
    db.commit()
    db.refresh(db_property)
    return db_property


def admin_unpublish_property(db: Session, db_property: Property, reason: Optional[str] = None) -> Property:
    """管理员强制下架（变为草稿和未发布状态，房东可修改后重新提交）"""
    if db_property.status == PropertyStatus.RENTED.value:
        raise ValueError(f"当前房源状态({db_property.status})不允许下架")
    
    db_property.status = PropertyStatus.UNPUBLISHED.value
    db_property.review_status = PropertyReviewStatus.DRAFT.value
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
                func.sum(case((Property.status == "published", 1), else_=0)), 0
            ).label("published_properties"),
            func.coalesce(
                func.sum(case((Property.status == "rented", 1), else_=0)), 0
            ).label("rented_properties"),
            func.coalesce(
                func.sum(case((Property.status == "unpublished", 1), else_=0)), 0
            ).label("unpublished_properties"),
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
            "published_properties": row.published_properties,
            "rented_properties": row.rented_properties,
            "unpublished_properties": row.unpublished_properties,
        }
        for row in results
    ]
