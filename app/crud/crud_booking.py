from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingUpdate


def get_booking(db: Session, booking_id: int) -> Optional[Booking]:
    return db.query(Booking).filter(Booking.id == booking_id).first()


def get_bookings(
    db: Session,
    tenant_id: Optional[int] = None,
    property_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[Booking]:
    query = db.query(Booking)
    if tenant_id is not None:
        query = query.filter(Booking.tenant_id == tenant_id)
    if property_id is not None:
        query = query.filter(Booking.property_id == property_id)
    if status is not None:
        query = query.filter(Booking.status == status)
    return query.offset(skip).limit(limit).all()


def create_booking(db: Session, tenant_id: int, booking_in: BookingCreate) -> Booking:
    booking = Booking(
        tenant_id=tenant_id,
        property_id=booking_in.property_id,
        appointment_time=booking_in.appointment_time,
        note=booking_in.note,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def update_booking(db: Session, db_booking: Booking, booking_in: BookingUpdate) -> Booking:
    for field, value in booking_in.dict(exclude_unset=True).items():
        setattr(db_booking, field, value)
    db.commit()
    db.refresh(db_booking)
    return db_booking


def delete_booking(db: Session, db_booking: Booking) -> Booking:
    db.delete(db_booking)
    db.commit()
    return db_booking
