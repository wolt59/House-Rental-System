from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.property import Property
from app.models.message import Message as MessageModel
from app.schemas.contract_application import (
    ContractApplicationCreate,
    ContractApplicationResponse,
    ContractApplication as ContractApplicationSchema
)
from app.crud import crud_contract_application, crud_message
from app.core.enums import UserRole, MessageType
from app.api.websocket import ws_manager

router = APIRouter()


def _notify_user(
    db: Session,
    from_user_id: int,
    to_user_id: int,
    content: str,
    property_id: Optional[int] = None,
    link: Optional[str] = None,
    background_tasks: Optional[BackgroundTasks] = None,
):
    notification = MessageModel(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        content=content,
        property_id=property_id,
        link=link,
        is_read=False,
        message_type=MessageType.NOTIFICATION.value,
    )
    db.add(notification)
    db.flush()
    db.refresh(notification)

    if background_tasks:
        unread_before = crud_message.get_unread_count(db, user_id=to_user_id, message_type="notification")

        async def notify():
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
            await ws_manager.send_personal(payload, to_user_id)

        background_tasks.add_task(notify)


@router.post("/", response_model=ContractApplicationSchema, status_code=status.HTTP_201_CREATED)
def create_application(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks,
    application_in: ContractApplicationCreate,
):
    """租客发起合约申请（只有看房完成后才能发起）"""
    if current_user.role != UserRole.TENANT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有租客可以发起合约申请"
        )

    try:
        application = crud_contract_application.create_contract_application(
            db=db,
            tenant_id=current_user.id,
            application_in=application_in
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    property_obj = db.query(Property).filter(Property.id == application.property_id).first()
    if property_obj:
        _notify_user(
            db=db,
            from_user_id=current_user.id,
            to_user_id=property_obj.owner_id,
            content=f"租客「{current_user.full_name or current_user.username}」申请租赁您的房源「{property_obj.title}」，请登录系统查看并处理。",
            property_id=application.property_id,
            link="/landlord/contracts",
            background_tasks=background_tasks,
        )

    db.commit()
    db.refresh(application)
    return application


@router.get("/", response_model=List[ContractApplicationSchema])
def list_applications(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
    property_id: Optional[int] = None,
    status: Optional[str] = None,
):
    """获取合约申请列表（根据角色自动过滤）"""
    if current_user.role == UserRole.TENANT:
        applications = crud_contract_application.get_contract_applications(
            db=db,
            tenant_id=current_user.id,
            property_id=property_id,
            status=status,
            skip=skip,
            limit=limit
        )
    elif current_user.role == UserRole.LANDLORD:
        applications = crud_contract_application.get_contract_applications(
            db=db,
            landlord_id=current_user.id,
            property_id=property_id,
            status=status,
            skip=skip,
            limit=limit
        )
    else:
        applications = crud_contract_application.get_contract_applications(
            db=db,
            property_id=property_id,
            status=status,
            skip=skip,
            limit=limit
        )

    return applications


@router.get("/{application_id}", response_model=ContractApplicationSchema)
def get_application(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    application_id: int,
):
    """获取单个合约申请详情"""
    application = crud_contract_application.get_contract_application(
        db=db,
        application_id=application_id
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合约申请不存在"
        )

    if current_user.role == UserRole.TENANT and application.tenant_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看此申请")
    if current_user.role == UserRole.LANDLORD and application.landlord_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看此申请")

    return application


@router.post("/{application_id}/approve", response_model=ContractApplicationSchema)
def approve_application(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks,
    application_id: int,
    response_data: ContractApplicationResponse,
):
    """房东同意合约申请，生成合同草稿"""
    if current_user.role != UserRole.LANDLORD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有房东可以处理合约申请"
        )

    application = crud_contract_application.get_contract_application(
        db=db,
        application_id=application_id
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合约申请不存在"
        )

    try:
        application = crud_contract_application.approve_contract_application(
            db=db,
            application=application,
            landlord_id=current_user.id,
            response=response_data.response
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    _notify_user(
        db=db,
        from_user_id=current_user.id,
        to_user_id=application.tenant_id,
        content=f"您的合约申请已被房东同意，已生成合同草稿（编号：{application.contract.contract_no if application.contract else ''}），请登录系统查看。",
        property_id=application.property_id,
        link="/tenant/contracts",
        background_tasks=background_tasks,
    )

    db.commit()
    db.refresh(application)
    return application


@router.post("/{application_id}/reject", response_model=ContractApplicationSchema)
def reject_application(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks,
    application_id: int,
    reason: str,
):
    """房东拒绝合约申请"""
    if current_user.role != UserRole.LANDLORD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有房东可以处理合约申请"
        )

    application = crud_contract_application.get_contract_application(
        db=db,
        application_id=application_id
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合约申请不存在"
        )

    try:
        application = crud_contract_application.reject_contract_application(
            db=db,
            application=application,
            landlord_id=current_user.id,
            reason=reason
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    _notify_user(
        db=db,
        from_user_id=current_user.id,
        to_user_id=application.tenant_id,
        content=f"您的合约申请已被房东拒绝。原因：{reason}",
        property_id=application.property_id,
        link="/tenant/contracts",
        background_tasks=background_tasks,
    )

    db.commit()
    db.refresh(application)
    return application


@router.post("/{application_id}/cancel", response_model=ContractApplicationSchema)
def cancel_application(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks,
    application_id: int,
):
    """租客取消合约申请"""
    if current_user.role != UserRole.TENANT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有租客可以取消合约申请"
        )

    application = crud_contract_application.get_contract_application(
        db=db,
        application_id=application_id
    )

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合约申请不存在"
        )

    try:
        application = crud_contract_application.cancel_contract_application(
            db=db,
            application=application,
            tenant_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    property_obj = db.query(Property).filter(Property.id == application.property_id).first()
    if property_obj:
        _notify_user(
            db=db,
            from_user_id=current_user.id,
            to_user_id=property_obj.owner_id,
            content=f"租客「{current_user.full_name or current_user.username}」已取消对房源「{property_obj.title}」的合约申请。",
            property_id=application.property_id,
            link="/landlord/contracts",
            background_tasks=background_tasks,
        )

    db.commit()
    db.refresh(application)
    return application