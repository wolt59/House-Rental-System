from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_landlord, get_current_active_user, get_current_active_admin, get_db
from app.crud import crud_audit, crud_booking, crud_message
from app.models.booking import Booking
from app.models.message import Message as MessageModel
from app.models.property import Property
from app.models.user import User
from app.schemas.booking import BookingCreate, Booking as BookingSchema, BookingUpdate, BookingReschedule, BookingRescheduleResponse
from app.core.enums import BookingStatus
from app.api.websocket import ws_manager

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
def create_booking(booking_in: BookingCreate, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    if current_user.role != "tenant":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only tenants can create bookings")

    property_obj = db.query(Property).filter(Property.id == booking_in.property_id).first()
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    # 修复时区比较问题：将前端时间转换为UTC时间（去除时区信息）
    appointment_utc = booking_in.appointment_time.replace(tzinfo=None) if booking_in.appointment_time.tzinfo else booking_in.appointment_time
    if appointment_utc < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot book in the past")

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

    landlord = db.query(User).filter(User.id == property_obj.owner_id).first()
    if landlord:
        content = f"租客「{current_user.full_name or current_user.username}」预约了您的房源「{property_obj.title}」看房，预约时间：{booking_in.appointment_time.strftime('%Y-%m-%d %H:%M')}。"
        link = f"/landlord/bookings"
        notification = MessageModel(
            from_user_id=current_user.id,
            to_user_id=landlord.id,
            property_id=booking.property_id,
            content=content,
            message_type="notification",
            link=link,
        )
        db.add(notification)
        db.commit()

        unread_before = crud_message.get_unread_count(db, user_id=landlord.id)

        async def notify_landlord():
            payload = {
                "type": "new_message",
                "message": {
                    "from_user_id": current_user.id,
                    "to_user_id": landlord.id,
                    "content": content,
                    "message_type": "notification",
                    "property_id": booking.property_id,
                    "link": link,
                    "is_read": False,
                },
                "unread_count": unread_before + 1,
            }
            await ws_manager.send_personal(payload, landlord.id)

        background_tasks.add_task(notify_landlord)

    return booking



@router.get("/", response_model=List[BookingSchema])
def list_bookings(
        db: Session = Depends(get_db),
        current_user=Depends(get_current_active_user),
        status: Optional[str] = Query(None),
        skip: int = Query(0),
        limit: int = Query(20)
):
    query = db.query(Booking).options(
        joinedload(Booking.tenant),
        joinedload(Booking.property).joinedload(Property.owner)
    )
    if current_user.role == "tenant":
        query = query.filter(Booking.tenant_id == current_user.id)
    elif current_user.role == "landlord":
        query = query.join(Property).filter(Property.owner_id == current_user.id)

    if status:
        # 支持逗号分隔的多个状态值
        status_list = [s.strip() for s in status.split(',')]
        if len(status_list) == 1:
            query = query.filter(Booking.status == status_list[0])
        else:
            query = query.filter(Booking.status.in_(status_list))

    return query.offset(skip).limit(limit).all()


@router.get("/{booking_id}", response_model=BookingSchema)
def read_booking(booking_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    booking = db.query(Booking).options(
        joinedload(Booking.tenant),
        joinedload(Booking.property).joinedload(Property.owner)
    ).filter(Booking.id == booking_id).first()
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
        if booking.status not in [BookingStatus.PENDING, BookingStatus.NEGOTIATING]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot update this booking")
        if booking_in.status and booking_in.status not in [BookingStatus.CANCELLED]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant may only cancel the booking")
    else:
        if booking_in.status and booking_in.status not in [BookingStatus.APPROVED, BookingStatus.REJECTED, BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
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


@router.post("/{booking_id}/approve", response_model=BookingSchema)
def approve_booking(booking_id: int, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_landlord)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    _authorize_booking(booking, current_user)

    if booking.status != BookingStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending bookings can be approved")

    updated = crud_booking.approve_booking(db, booking)

    tenant = db.query(User).filter(User.id == booking.tenant_id).first()
    if tenant:
        content = f"房东「{current_user.full_name or current_user.username}」已同意您对房源「{booking.property.title}」的看房预约。"
        link = f"/tenant/bookings"
        notification = MessageModel(
            from_user_id=current_user.id,
            to_user_id=tenant.id,
            property_id=booking.property_id,
            content=content,
            message_type="notification",
            link=link,
        )
        db.add(notification)
        db.commit()

        unread_before = crud_message.get_unread_count(db, user_id=tenant.id)

        async def notify_tenant():
            payload = {
                "type": "new_message",
                "message": {
                    "from_user_id": current_user.id,
                    "to_user_id": tenant.id,
                    "content": content,
                    "message_type": "notification",
                    "property_id": booking.property_id,
                    "link": link,
                    "is_read": False,
                },
                "unread_count": unread_before + 1,
            }
            await ws_manager.send_personal(payload, tenant.id)

        background_tasks.add_task(notify_tenant)

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="approve_booking",
        target_type="booking",
        target_id=updated.id,
        detail="Booking approved",
        ip_address=ip_address,
    )
    return updated


@router.post("/{booking_id}/reject", response_model=BookingSchema)
def reject_booking(booking_id: int, reason: str, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_landlord)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    _authorize_booking(booking, current_user)

    if booking.status != BookingStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending bookings can be rejected")

    if not reason or len(reason.strip()) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reject reason is required")

    updated = crud_booking.reject_booking(db, booking, reason)

    tenant = db.query(User).filter(User.id == booking.tenant_id).first()
    if tenant:
        content = f"房东「{current_user.full_name or current_user.username}」拒绝了您对房源「{booking.property.title}」的看房预约。原因：{reason}"
        link = f"/tenant/bookings"
        notification = MessageModel(
            from_user_id=current_user.id,
            to_user_id=tenant.id,
            property_id=booking.property_id,
            content=content,
            message_type="notification",
            link=link,
        )
        db.add(notification)
        db.commit()

        unread_before = crud_message.get_unread_count(db, user_id=tenant.id)

        async def notify_tenant():
            payload = {
                "type": "new_message",
                "message": {
                    "from_user_id": current_user.id,
                    "to_user_id": tenant.id,
                    "content": content,
                    "message_type": "notification",
                    "property_id": booking.property_id,
                    "link": link,
                    "is_read": False,
                },
                "unread_count": unread_before + 1,
            }
            await ws_manager.send_personal(payload, tenant.id)

        background_tasks.add_task(notify_tenant)

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="reject_booking",
        target_type="booking",
        target_id=updated.id,
        detail=f"Booking rejected: {reason}",
        ip_address=ip_address,
    )
    return updated


@router.post("/{booking_id}/reschedule", response_model=BookingSchema)
def reschedule_booking(booking_id: int, reschedule: BookingReschedule, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_landlord)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    _authorize_booking(booking, current_user)

    if booking.status not in [BookingStatus.PENDING, BookingStatus.APPROVED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot reschedule this booking")

    updated = crud_booking.propose_reschedule(db, booking, reschedule.appointment_time, reschedule.message)

    tenant = db.query(User).filter(User.id == booking.tenant_id).first()
    if tenant:
        content = f"房东「{current_user.full_name or current_user.username}」提议改期看房「{booking.property.title}」，新时间：{reschedule.appointment_time.strftime('%Y-%m-%d %H:%M')}。留言：{reschedule.message or '无'}"
        link = f"/tenant/bookings"
        notification = MessageModel(
            from_user_id=current_user.id,
            to_user_id=tenant.id,
            property_id=booking.property_id,
            content=content,
            message_type="notification",
            link=link,
        )
        db.add(notification)
        db.commit()

        unread_before = crud_message.get_unread_count(db, user_id=tenant.id)

        async def notify_tenant():
            payload = {
                "type": "new_message",
                "message": {
                    "from_user_id": current_user.id,
                    "to_user_id": tenant.id,
                    "content": content,
                    "message_type": "notification",
                    "property_id": booking.property_id,
                    "link": link,
                    "is_read": False,
                },
                "unread_count": unread_before + 1,
            }
            await ws_manager.send_personal(payload, tenant.id)

        background_tasks.add_task(notify_tenant)

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="reschedule_booking",
        target_type="booking",
        target_id=updated.id,
        detail=f"Booking reschedule proposed: {reschedule.message}",
        ip_address=ip_address,
    )
    return updated


@router.post("/{booking_id}/reschedule-response", response_model=BookingSchema)
def respond_reschedule(booking_id: int, response: BookingRescheduleResponse, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    _authorize_booking(booking, current_user)
    
    if booking.status != BookingStatus.NEGOTIATING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No pending reschedule request")
    
    if response.response == "accept":
        booking.status = BookingStatus.APPROVED
        booking.reschedule_response = "accepted"
        booking.confirmed_at = datetime.utcnow()
    elif response.response == "reject":
        booking.status = BookingStatus.PENDING
        booking.reschedule_response = "rejected"
        booking.reschedule_proposal = None
    elif response.response == "cancel":
        booking.status = BookingStatus.CANCELLED
        booking.reschedule_response = "cancelled"
        booking.cancel_reason = response.message or "Cancelled during negotiation"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid response")
    
    db.commit()
    db.refresh(booking)
    
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="respond_reschedule",
        target_type="booking",
        target_id=booking.id,
        detail=f"Reschedule response: {response.response}",
        ip_address=ip_address,
    )
    return booking


@router.post("/{booking_id}/complete", response_model=BookingSchema)
def complete_booking(booking_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    _authorize_booking(booking, current_user)
    
    if booking.status != BookingStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only approved bookings can be completed")
    
    updated = crud_booking.complete_booking(db, booking)
    
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="complete_booking",
        target_type="booking",
        target_id=updated.id,
        detail="Booking marked as completed",
        ip_address=ip_address,
    )
    return updated


@router.post("/{booking_id}/show-contact", response_model=BookingSchema)
def show_contact_info(booking_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    _authorize_booking(booking, current_user)
    
    if booking.status != BookingStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contact info only available for approved bookings")
    
    booking.landlord_contact_shown = 1
    db.commit()
    db.refresh(booking)
    
    return booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    _authorize_booking(booking, current_user)

    if current_user.role == "tenant" and booking.status not in [BookingStatus.PENDING, BookingStatus.CANCELLED, BookingStatus.REJECTED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete this booking")

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
