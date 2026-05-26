from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_landlord, get_current_active_user, get_current_active_admin, get_db
from app.crud import crud_audit
from app.models.booking import Booking
from app.models.property import Property
from app.schemas.booking import BookingCreate, Booking as BookingSchema, BookingUpdate
from app.core.enums import BookingStatus

router = APIRouter()


def _authorize_booking(booking: Booking, current_user):
    if current_user.role == "admin":
        return
    if current_user.role == "landlord":
        if booking.property.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to manage this booking")
        return
    if current_user.role == "tenant" and booking.tenant_id == current_user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


@router.post("/", response_model=BookingSchema, status_code=status.HTTP_201_CREATED)
def create_booking(booking_in: BookingCreate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    property_obj = db.query(Property).filter(Property.id == booking_in.property_id).first()
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    booking = Booking(
        tenant_id=current_user.id,
        property_id=booking_in.property_id,
        appointment_time=booking_in.appointment_time,
        note=booking_in.note,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="create_booking",
        target_type="booking",
        target_id=booking.id,
        detail=f"Booking created for property {booking.property_id}",
        ip_address=ip_address,
    )
    return booking


@router.get("/", response_model=List[BookingSchema])
def list_bookings(db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    query = db.query(Booking)
    if current_user.role == "tenant":
        query = query.filter(Booking.tenant_id == current_user.id)
    elif current_user.role == "landlord":
        query = query.join(Property).filter(Property.owner_id == current_user.id)
    return query.all()


@router.get("/{booking_id}", response_model=BookingSchema)
def read_booking(booking_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    _authorize_booking(booking, current_user)
    return booking


@router.put("/{booking_id}", response_model=BookingSchema)
def update_booking(booking_id: int, booking_in: BookingUpdate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    _authorize_booking(booking, current_user)

    if current_user.role == "tenant":
        if booking.status != BookingStatus.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending bookings can be updated")
        if booking_in.status and booking_in.status != BookingStatus.CANCELLED:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant may only cancel the booking")
    else:
        if booking_in.status and booking_in.status not in {BookingStatus.APPROVED, BookingStatus.REJECTED, BookingStatus.CANCELLED}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid booking status")

    if booking_in.appointment_time is not None:
        booking.appointment_time = booking_in.appointment_time
    if booking_in.note is not None:
        booking.note = booking_in.note
    if booking_in.status is not None:
        booking.status = booking_in.status

    db.commit()
    db.refresh(booking)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_booking",
        target_type="booking",
        target_id=booking.id,
        detail=f"Booking updated, status={booking.status}",
        ip_address=ip_address,
    )
    return booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    _authorize_booking(booking, current_user)

    if current_user.role == "tenant" and booking.status != BookingStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending bookings can be deleted")

    db.delete(booking)
    db.commit()
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="delete_booking",
        target_type="booking",
        target_id=booking.id,
        detail="Booking deleted",
        ip_address=ip_address,
    )
    return None
