from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingUpdate
from app.core.enums import BookingStatus


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
        status=BookingStatus.PENDING,
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


def approve_booking(db: Session, db_booking: Booking) -> Booking:
    db_booking.status = BookingStatus.APPROVED
    db_booking.confirmed_at = db_booking.updated_at
    db.commit()
    db.refresh(db_booking)
    return db_booking


def reject_booking(db: Session, db_booking: Booking, reason: str) -> Booking:
    db_booking.status = BookingStatus.REJECTED
    db_booking.reject_reason = reason
    db.commit()
    db.refresh(db_booking)
    return db_booking


def propose_reschedule(db: Session, db_booking: Booking, new_time, message: str) -> Booking:
    db_booking.status = BookingStatus.NEGOTIATING
    db_booking.reschedule_proposal = message
    db_booking.appointment_time = new_time
    db.commit()
    db.refresh(db_booking)
    return db_booking


def complete_booking(db: Session, db_booking: Booking) -> Booking:
    db_booking.status = BookingStatus.COMPLETED
    db_booking.completed_at = db_booking.updated_at
    db.commit()
    db.refresh(db_booking)
    return db_booking


def delete_booking(db: Session, db_booking: Booking) -> Booking:
    db.delete(db_booking)
    db.commit()
    return db_booking
