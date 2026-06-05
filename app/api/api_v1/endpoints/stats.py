from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.api.deps import get_current_active_admin, get_current_active_landlord, get_db
from app.cache import cache_manager, CacheKey
from app.core.config import settings
from app.models.property import Property
from app.models.contract import Contract
from app.models.payment import Payment
from app.models.user import User
from app.models.booking import Booking
from app.models.maintenance import MaintenanceRequest
from app.models.complaint import Complaint
from app.schemas.property import RegionStats, FloorPlanStats
from app.core.enums import PropertyReviewStatus, PropertyStatus, ContractStatus, PaymentStatus, BookingStatus, MaintenanceStatus, ComplaintStatus

router = APIRouter()


@router.get("/regions", response_model=List[RegionStats])
def search_by_region(db: Session = Depends(get_db)):
    cache_key = CacheKey.stats("regions")
    return cache_manager.get_or_set(cache_key, lambda: _query_regions(db), ttl=settings.CACHE_LONG_TTL)


def _query_regions(db: Session):
    results = (
        db.query(Property.region, func.count(Property.id).label("property_count"))
        .filter(Property.review_status == PropertyReviewStatus.APPROVED, Property.region.isnot(None))
        .group_by(Property.region)
        .order_by(func.count(Property.id).desc())
        .all()
    )
    return [RegionStats(region=r.region, property_count=r.property_count) for r in results]


@router.get("/floor-plans", response_model=List[FloorPlanStats])
def search_by_floor_plan(db: Session = Depends(get_db)):
    cache_key = CacheKey.stats("floor_plans")
    return cache_manager.get_or_set(cache_key, lambda: _query_floor_plans(db), ttl=settings.CACHE_LONG_TTL)


def _query_floor_plans(db: Session):
    results = (
        db.query(Property.floor_plan, func.count(Property.id).label("property_count"))
        .filter(Property.review_status == PropertyReviewStatus.APPROVED, Property.floor_plan.isnot(None))
        .group_by(Property.floor_plan)
        .order_by(func.count(Property.id).desc())
        .all()
    )
    return [FloorPlanStats(floor_plan=r.floor_plan, property_count=r.property_count) for r in results]


@router.get("/dashboard")
def admin_dashboard(db: Session = Depends(get_db), current_user=Depends(get_current_active_admin)):
    cache_key = CacheKey.dashboard_stats()
    return cache_manager.get_or_set(cache_key, lambda: _query_admin_dashboard(db), ttl=settings.CACHE_SHORT_TTL)


def _query_admin_dashboard(db: Session):
    total_users = db.query(func.count(User.id)).scalar()
    total_properties = db.query(func.count(Property.id)).scalar()
    approved_properties = db.query(func.count(Property.id)).filter(Property.review_status == PropertyReviewStatus.APPROVED).scalar()
    published_properties = db.query(func.count(Property.id)).filter(Property.status == PropertyStatus.PUBLISHED).scalar()
    rented_properties = db.query(func.count(Property.id)).filter(Property.status == PropertyStatus.RENTED).scalar()
    total_contracts = db.query(func.count(Contract.id)).scalar()
    active_contracts = db.query(func.count(Contract.id)).filter(Contract.status == ContractStatus.ACTIVE).scalar()
    total_payments = db.query(func.count(Payment.id)).scalar()
    paid_payments = db.query(func.count(Payment.id)).filter(Payment.status == PaymentStatus.PAID).scalar()
    pending_payments = db.query(func.count(Payment.id)).filter(Payment.status == PaymentStatus.PENDING).scalar()
    total_rent_income = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.status == PaymentStatus.PAID).scalar()
    total_bookings = db.query(func.count(Booking.id)).scalar()
    pending_bookings = db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.PENDING).scalar()
    open_maintenance = db.query(func.count(MaintenanceRequest.id)).filter(MaintenanceRequest.status == MaintenanceStatus.NEW).scalar()
    open_complaints = db.query(func.count(Complaint.id)).filter(Complaint.status == ComplaintStatus.OPEN).scalar()
    occupancy_rate = round(rented_properties / approved_properties * 100, 1) if approved_properties > 0 else 0

    return {
        "users": {"total": total_users},
        "properties": {
            "total": total_properties,
            "approved": approved_properties,
            "published": published_properties,
            "rented": rented_properties,
            "occupancy_rate": occupancy_rate,
        },
        "contracts": {"total": total_contracts, "active": active_contracts},
        "payments": {
            "total": total_payments,
            "paid": paid_payments,
            "pending": pending_payments,
            "total_rent_income": float(total_rent_income),
        },
        "bookings": {"total": total_bookings, "pending": pending_bookings},
        "maintenance": {"open": open_maintenance},
        "complaints": {"open": open_complaints},
    }


@router.get("/monthly-income")
def get_monthly_income(db: Session = Depends(get_db), current_user=Depends(get_current_active_admin)):
    """获取近 6 个月的租金收入趋势"""
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    results = (
        db.query(
            extract('year', Payment.created_at).label('year'),
            extract('month', Payment.created_at).label('month'),
            func.coalesce(func.sum(Payment.amount), 0).label('total_amount')
        )
        .filter(Payment.status == "paid", Payment.created_at >= six_months_ago)
        .group_by('year', 'month')
        .order_by('year', 'month')
        .all()
    )

    monthly_data = []
    for r in results:
        month_str = f"{int(r.year)}-{int(r.month):02d}"
        monthly_data.append({
            "month": month_str,
            "amount": float(r.total_amount)
        })

    return monthly_data


@router.get("/user-activity")
def get_user_activity(db: Session = Depends(get_db), current_user=Depends(get_current_active_admin)):
    """获取用户活跃度统计"""
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()

    tenant_count = db.query(func.count(User.id)).filter(User.role == "tenant").scalar()
    landlord_count = db.query(func.count(User.id)).filter(User.role == "landlord").scalar()
    admin_count = db.query(func.count(User.id)).filter(User.role == "admin").scalar()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "role_distribution": {
            "tenant": tenant_count,
            "landlord": landlord_count,
            "admin": admin_count
        }
    }


@router.get("/property-status")
def get_property_status(db: Session = Depends(get_db), current_user=Depends(get_current_active_admin)):
    """获取房源状态分布"""
    total = db.query(func.count(Property.id)).scalar()
    published = db.query(func.count(Property.id)).filter(Property.status == PropertyStatus.PUBLISHED).scalar()
    rented = db.query(func.count(Property.id)).filter(Property.status == PropertyStatus.RENTED).scalar()
    unpublished = db.query(func.count(Property.id)).filter(Property.status == PropertyStatus.UNPUBLISHED).scalar()
    pending = db.query(func.count(Property.id)).filter(Property.review_status == PropertyReviewStatus.PENDING).scalar()

    return {
        "total": total,
        "published": published or 0,
        "rented": rented or 0,
        "unpublished": unpublished or 0,
        "pending_review": pending or 0
    }


@router.get("/landlord-dashboard")
def landlord_dashboard(db: Session = Depends(get_db), current_user=Depends(get_current_active_landlord)):
    """房东专属统计面板"""
    cache_key = CacheKey.stats(f"landlord_dashboard:{current_user.id}")
    return cache_manager.get_or_set(cache_key, lambda: _query_landlord_dashboard(db, current_user.id), ttl=settings.CACHE_SHORT_TTL)


def _query_landlord_dashboard(db: Session, landlord_id: int):

    total_properties = db.query(func.count(Property.id)).filter(Property.owner_id == landlord_id).scalar()
    published_properties = db.query(func.count(Property.id)).filter(
        Property.owner_id == landlord_id, Property.status == "published"
    ).scalar()
    rented_properties = db.query(func.count(Property.id)).filter(
        Property.owner_id == landlord_id, Property.status == "rented"
    ).scalar()

    occupancy_rate = round(rented_properties / total_properties * 100, 1) if total_properties > 0 else 0

    total_income = db.query(func.coalesce(func.sum(Payment.amount), 0)).join(
        Contract, Payment.contract_id == Contract.id
    ).filter(
        Contract.landlord_id == landlord_id,
        Payment.status == "paid"
    ).scalar()

    pending_bookings = db.query(func.count(Booking.id)).join(
        Property, Booking.property_id == Property.id
    ).filter(
        Property.owner_id == landlord_id,
        Booking.status == "pending"
    ).scalar()

    open_maintenance = db.query(func.count(MaintenanceRequest.id)).join(
        Property, MaintenanceRequest.property_id == Property.id
    ).filter(
        Property.owner_id == landlord_id,
        MaintenanceRequest.status == "new"
    ).scalar()

    open_complaints = db.query(func.count(Complaint.id)).join(
        Property, Complaint.property_id == Property.id
    ).filter(
        Property.owner_id == landlord_id,
        Complaint.status == "open"
    ).scalar()

    return {
        "properties": {
            "total": total_properties,
            "published": published_properties,
            "rented": rented_properties,
            "occupancy_rate": occupancy_rate
        },
        "income": {
            "total": float(total_income)
        },
        "bookings": {
            "pending": pending_bookings
        },
        "maintenance": {
            "open": open_maintenance
        },
        "complaints": {
            "open": open_complaints
        }
    }


@router.get("/landlord-monthly-income")
def get_landlord_monthly_income(db: Session = Depends(get_db), current_user=Depends(get_current_active_landlord)):
    """房东近 6 个月收入趋势"""
    landlord_id = current_user.id
    six_months_ago = datetime.utcnow() - timedelta(days=180)

    results = (
        db.query(
            extract('year', Payment.created_at).label('year'),
            extract('month', Payment.created_at).label('month'),
            func.coalesce(func.sum(Payment.amount), 0).label('total_amount')
        )
        .join(Contract, Payment.contract_id == Contract.id)
        .filter(
            Contract.landlord_id == landlord_id,
            Payment.status == "paid",
            Payment.created_at >= six_months_ago
        )
        .group_by('year', 'month')
        .order_by('year', 'month')
        .all()
    )

    monthly_data = []
    for r in results:
        month_str = f"{int(r.year)}-{int(r.month):02d}"
        monthly_data.append({
            "month": month_str,
            "amount": float(r.total_amount)
        })

    return monthly_data
