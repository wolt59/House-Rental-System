from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_landlord, get_current_active_user, get_current_active_admin, get_db
from app.crud import crud_audit, crud_booking
from app.models.booking import Booking
from app.models.property import Property
from app.schemas.booking import BookingCreate, Booking as BookingSchema, BookingUpdate

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
    if property_obj.review_status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Property is not available for booking")
    booking = crud_booking.create_booking(db, tenant_id=current_user.id, booking_in=booking_in)
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
def list_bookings(
    skip: int = 0,
    limit: int = 20,
    status: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    query = db.query(Booking)
    if current_user.role == "tenant":
        query = query.filter(Booking.tenant_id == current_user.id)
    elif current_user.role == "landlord":
        query = query.join(Property).filter(Property.owner_id == current_user.id)
    if status is not None:
        query = query.filter(Booking.status == status)
    return query.offset(skip).limit(limit).all()


@router.get("/{booking_id}", response_model=BookingSchema)
def read_booking(booking_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    booking = crud_booking.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    _authorize_booking(booking, current_user)
    return booking


@router.put("/{booking_id}", response_model=BookingSchema)
def update_booking(booking_id: int, booking_in: BookingUpdate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    booking = crud_booking.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    _authorize_booking(booking, current_user)

    if current_user.role == "tenant":
        if booking.status != "pending":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending bookings can be updated")
        if booking_in.status and booking_in.status != "cancelled":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant may only cancel the booking")
    else:
        if booking_in.status and booking_in.status not in {"approved", "rejected", "cancelled"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid booking status")

    updated = crud_booking.update_booking(db, booking, booking_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_booking",
        target_type="booking",
        target_id=updated.id,
        detail=f"Booking updated, status={updated.status}",
        ip_address=ip_address,
    )
    return updated


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    booking = crud_booking.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    _authorize_booking(booking, current_user)

    if current_user.role == "tenant" and booking.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending bookings can be deleted")

    crud_booking.delete_booking(db, booking)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="delete_booking",
        target_type="booking",
        target_id=booking_id,
        detail="Booking deleted",
        ip_address=ip_address,
    )
    return None
