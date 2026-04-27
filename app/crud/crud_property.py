from typing import List, Optional
from sqlalchemy import case, func
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
    return query.offset(skip).limit(limit).all()


def create_property(db: Session, owner_id: int, property_in: PropertyCreate) -> Property:
    data = property_in.dict()
    data["owner_id"] = owner_id
    data["review_status"] = "pending"
    if not data.get("status"):
        data["status"] = "vacant"
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
