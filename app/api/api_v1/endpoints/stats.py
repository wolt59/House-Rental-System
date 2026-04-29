from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.api.deps import get_current_active_admin, get_current_active_landlord, get_db
from app.models.property import Property
from app.models.contract import Contract
from app.models.payment import Payment
from app.models.user import User
from app.models.booking import Booking
from app.models.maintenance import MaintenanceRequest
from app.models.complaint import Complaint
from app.schemas.property import RegionStats, FloorPlanStats

router = APIRouter()


@router.get("/regions", response_model=List[RegionStats])
def search_by_region(db: Session = Depends(get_db)):
    results = (
        db.query(Property.region, func.count(Property.id).label("property_count"))
        .filter(Property.review_status == "approved", Property.region.isnot(None))
        .group_by(Property.region)
        .order_by(func.count(Property.id).desc())
        .all()
    )
    return [RegionStats(region=r.region, property_count=r.property_count) for r in results]


@router.get("/floor-plans", response_model=List[FloorPlanStats])
def search_by_floor_plan(db: Session = Depends(get_db)):
    results = (
        db.query(Property.floor_plan, func.count(Property.id).label("property_count"))
        .filter(Property.review_status == "approved", Property.floor_plan.isnot(None))
        .group_by(Property.floor_plan)
        .order_by(func.count(Property.id).desc())
        .all()
    )
    return [FloorPlanStats(floor_plan=r.floor_plan, property_count=r.property_count) for r in results]


@router.get("/dashboard")
def admin_dashboard(db: Session = Depends(get_db), current_user=Depends(get_current_active_admin)):
    total_users = db.query(func.count(User.id)).scalar()
    total_properties = db.query(func.count(Property.id)).scalar()
    approved_properties = db.query(func.count(Property.id)).filter(Property.review_status == "approved").scalar()
    vacant_properties = db.query(func.count(Property.id)).filter(Property.status == "vacant").scalar()
    rented_properties = db.query(func.count(Property.id)).filter(Property.status == "rented").scalar()
    total_contracts = db.query(func.count(Contract.id)).scalar()
    active_contracts = db.query(func.count(Contract.id)).filter(Contract.status == "active").scalar()
    total_payments = db.query(func.count(Payment.id)).scalar()
    paid_payments = db.query(func.count(Payment.id)).filter(Payment.status == "paid").scalar()
    pending_payments = db.query(func.count(Payment.id)).filter(Payment.status == "pending").scalar()
    total_rent_income = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.status == "paid").scalar()
    total_bookings = db.query(func.count(Booking.id)).scalar()
    pending_bookings = db.query(func.count(Booking.id)).filter(Booking.status == "pending").scalar()
    open_maintenance = db.query(func.count(MaintenanceRequest.id)).filter(MaintenanceRequest.status == "new").scalar()
    open_complaints = db.query(func.count(Complaint.id)).filter(Complaint.status == "open").scalar()
    occupancy_rate = round(rented_properties / approved_properties * 100, 1) if approved_properties > 0 else 0

    return {
        "users": {"total": total_users},
        "properties": {
            "total": total_properties,
            "approved": approved_properties,
            "vacant": vacant_properties,
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
    vacant = db.query(func.count(Property.id)).filter(Property.status == "vacant").scalar()
    rented = db.query(func.count(Property.id)).filter(Property.status == "rented").scalar()
    maintenance = db.query(func.count(Property.id)).filter(Property.status == "maintenance").scalar()
    pending = db.query(func.count(Property.id)).filter(Property.review_status == "pending").scalar()

    return {
        "total": total,
        "vacant": vacant or 0,
        "rented": rented or 0,
        "maintenance": maintenance or 0,
        "pending_review": pending or 0
    }


@router.get("/landlord-dashboard")
def landlord_dashboard(db: Session = Depends(get_db), current_user=Depends(get_current_active_landlord)):
    """房东专属统计面板"""
    landlord_id = current_user.id

    total_properties = db.query(func.count(Property.id)).filter(Property.owner_id == landlord_id).scalar()
    vacant_properties = db.query(func.count(Property.id)).filter(
        Property.owner_id == landlord_id, Property.status == "vacant"
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
            "vacant": vacant_properties,
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
