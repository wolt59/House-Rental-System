from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_landlord, get_current_active_user, get_current_active_admin, get_db
from app.schemas.common import PaginatedResponse
from app.crud import crud_audit, crud_maintenance, crud_message
from app.models.maintenance import MaintenanceRequest
from app.models.message import Message as MessageModel
from app.models.property import Property
from app.models.user import User
from app.schemas.maintenance import Maintenance, MaintenanceCreate, MaintenanceUpdate
from app.core.enums import MaintenanceStatus
from app.api.websocket import ws_manager

router = APIRouter()


def _authorize_maintenance(request: MaintenanceRequest, current_user):
    if current_user.role == "admin":
        return
    if current_user.role == "landlord":
        if request.property.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to manage this request")
        return
    if current_user.role == "tenant" and request.tenant_id == current_user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


@router.post("/", response_model=Maintenance, status_code=status.HTTP_201_CREATED)
def create_maintenance(
    request_in: MaintenanceCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    if current_user.role != "tenant":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only tenants can create maintenance requests")
    property_obj = db.query(Property).filter(Property.id == request_in.property_id).first()
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    maintenance = crud_maintenance.create_maintenance(db, tenant_id=current_user.id, maintenance_in=request_in)

    # 通知房东
    notification = MessageModel(
        from_user_id=current_user.id,
        to_user_id=property_obj.owner_id,
        property_id=maintenance.property_id,
        content=f"租客「{current_user.full_name or current_user.username}」提交了房源「{property_obj.title}」的维修申请，请登录系统查看并处理。",
        message_type="notification",
        link="/landlord/maintenance",
    )
    db.add(notification)
    db.flush()
    db.refresh(notification)
    db.commit()

    unread_before = crud_message.get_unread_count(db, user_id=property_obj.owner_id, message_type="notification")

    async def notify_landlord():
        payload = {
            "type": "new_message",
            "message": {
                "id": notification.id,
                "from_user_id": notification.from_user_id,
                "to_user_id": notification.to_user_id,
                "content": notification.content,
                "message_type": notification.message_type,
                "property_id": notification.property_id,
                "link": notification.link,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat() + 'Z' if notification.created_at else None,
            },
            "unread_count": unread_before + 1,
        }
        await ws_manager.send_personal(payload, property_obj.owner_id)

    background_tasks.add_task(notify_landlord)

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="create_maintenance",
        target_type="maintenance",
        target_id=maintenance.id,
        detail=f"Maintenance request created for property {maintenance.property_id}",
        ip_address=ip_address,
    )
    return maintenance


@router.get("/")
def list_maintenance(
    skip: int = 0,
    limit: int = 20,
    status: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    query = db.query(MaintenanceRequest)
    if current_user.role == "tenant":
        query = query.filter(MaintenanceRequest.tenant_id == current_user.id)
    elif current_user.role == "landlord":
        query = query.join(Property).filter(Property.owner_id == current_user.id)
    if status is not None:
        query = query.filter(MaintenanceRequest.status == status)
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    serialized_items = [Maintenance.model_validate(m).model_dump(mode='json') for m in items]
    return {"items": serialized_items, "total": total}


@router.get("/{request_id}", response_model=Maintenance)
def read_maintenance(request_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    request_item = crud_maintenance.get_maintenance(db, request_id)
    if not request_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance request not found")
    _authorize_maintenance(request_item, current_user)
    return request_item


@router.put("/{request_id}", response_model=Maintenance)
def update_maintenance(
    request_id: int,
    request_in: MaintenanceUpdate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    request_item = crud_maintenance.get_maintenance(db, request_id)
    if not request_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance request not found")
    _authorize_maintenance(request_item, current_user)

    if current_user.role == "tenant":
        if request_item.status != MaintenanceStatus.NEW:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only new maintenance requests can be updated by tenant")
        if request_in.status and request_in.status != MaintenanceStatus.NEW:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant cannot change status")
        if request_in.assigned_to is not None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant cannot assign maintenance tasks")
    else:
        if request_in.status and request_in.status not in {MaintenanceStatus.NEW, MaintenanceStatus.IN_PROGRESS, MaintenanceStatus.RESOLVED, MaintenanceStatus.CLOSED}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid maintenance status")

    updated = crud_maintenance.update_maintenance(db, request_item, request_in)

    # 非租客操作时，通知租客状态变更
    if current_user.role != "tenant" and updated.status != request_item.status:
        status_cn = {
            "new": "待处理",
            "in_progress": "处理中",
            "resolved": "已解决",
            "closed": "已关闭",
        }.get(updated.status, updated.status)
        notification = MessageModel(
            from_user_id=current_user.id,
            to_user_id=updated.tenant_id,
            property_id=updated.property_id,
            content=f"您的维修申请状态已更新为「{status_cn}」。",
            message_type="notification",
            link="/tenant/maintenance",
        )
        db.add(notification)
        db.flush()
        db.refresh(notification)
        db.commit()

        unread_before = crud_message.get_unread_count(db, user_id=updated.tenant_id, message_type="notification")

        async def notify_tenant():
            payload = {
                "type": "new_message",
                "message": {
                    "id": notification.id,
                    "from_user_id": notification.from_user_id,
                    "to_user_id": notification.to_user_id,
                    "content": notification.content,
                    "message_type": notification.message_type,
                    "property_id": notification.property_id,
                    "link": notification.link,
                    "is_read": notification.is_read,
                    "created_at": notification.created_at.isoformat() + 'Z' if notification.created_at else None,
                },
                "unread_count": unread_before + 1,
            }
            await ws_manager.send_personal(payload, updated.tenant_id)

        background_tasks.add_task(notify_tenant)

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_maintenance",
        target_type="maintenance",
        target_id=updated.id,
        detail=f"Maintenance request updated, status={updated.status}",
        ip_address=ip_address,
    )
    return updated
