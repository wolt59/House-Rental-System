from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_admin, get_db
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
