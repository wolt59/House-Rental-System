from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.message import Message as MessageModel
from app.schemas.contract_termination_request import (
    ContractTerminationRequestCreate,
    ContractTerminationRequest as ContractTerminationRequestSchema,
)
from app.crud import crud_contract_change, crud_message
from app.core.enums import UserRole, MessageType
from app.api.websocket import ws_manager

router = APIRouter()


def _notify_user(
    db: Session,
    from_user_id: int,
    to_user_id: int,
    content: str,
    property_id: Optional[int] = None,
    background_tasks: Optional[BackgroundTasks] = None,
):
    notification = MessageModel(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        content=content,
        property_id=property_id,
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
                    "is_read": notification.is_read,
                    "created_at": notification.created_at.isoformat() if notification.created_at else None,
                },
                "unread_count": unread_before + 1,
            }
            await ws_manager.send_personal(payload, to_user_id)

        background_tasks.add_task(notify)


@router.post("/", response_model=ContractTerminationRequestSchema, status_code=status.HTTP_201_CREATED)
def create_termination_request(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks,
    request_in: ContractTerminationRequestCreate,
):
    """发起提前解约申请"""
    try:
        termination_request = crud_contract_change.create_contract_termination_request(
            db=db,
            initiator_id=current_user.id,
            request_in=request_in
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    contract = termination_request.contract
    notify_user_id = contract.landlord_id if current_user.id == contract.tenant_id else contract.tenant_id
    _notify_user(
        db=db,
        from_user_id=current_user.id,
        to_user_id=notify_user_id,
        content=f"合同（编号：{contract.contract_no}）的提前解约申请已发起，解约原因：{termination_request.termination_reason}，请登录系统查看并处理。",
        property_id=contract.property_id,
        background_tasks=background_tasks,
    )

    db.commit()
    db.refresh(termination_request)
    return termination_request


@router.get("/", response_model=List[ContractTerminationRequestSchema])
def list_termination_requests(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
    contract_id: Optional[int] = None,
    status: Optional[str] = None,
):
    """获取提前解约申请列表"""
    if current_user.role == UserRole.TENANT:
        requests = crud_contract_change.get_contract_termination_requests_by_role(
            db=db,
            tenant_id=current_user.id,
            contract_id=contract_id,
            status=status,
            skip=skip,
            limit=limit
        )
    elif current_user.role == UserRole.LANDLORD:
        requests = crud_contract_change.get_contract_termination_requests_by_role(
            db=db,
            landlord_id=current_user.id,
            contract_id=contract_id,
            status=status,
            skip=skip,
            limit=limit
        )
    else:
        requests = crud_contract_change.get_contract_termination_requests(
            db=db,
            contract_id=contract_id,
            status=status,
            skip=skip,
            limit=limit
        )

    return requests


@router.get("/{request_id}", response_model=ContractTerminationRequestSchema)
def get_termination_request(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request_id: int,
):
    """获取单个提前解约申请详情"""
    termination_request = crud_contract_change.get_contract_termination_request(
        db=db,
        request_id=request_id
    )

    if not termination_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提前解约申请不存在"
        )

    contract = termination_request.contract
    if current_user.id not in [contract.tenant_id, contract.landlord_id]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看此申请")

    return termination_request


@router.post("/{request_id}/approve", response_model=ContractTerminationRequestSchema)
def approve_termination_request(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks,
    request_id: int,
    opinion: Optional[str] = None,
):
    """同意提前解约申请"""
    termination_request = crud_contract_change.get_contract_termination_request(
        db=db,
        request_id=request_id
    )

    if not termination_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提前解约申请不存在"
        )

    contract = termination_request.contract
    if current_user.id == termination_request.initiator_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="发起人不能审批自己的申请")
    if current_user.id not in [contract.tenant_id, contract.landlord_id]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权处理此申请")

    try:
        termination_request = crud_contract_change.approve_contract_termination_request(
            db=db,
            request=termination_request,
            responder_id=current_user.id,
            response_opinion=opinion
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    _notify_user(
        db=db,
        from_user_id=current_user.id,
        to_user_id=termination_request.initiator_id,
        content=f"合同（编号：{contract.contract_no}）的提前解约申请已被同意。",
        property_id=contract.property_id,
        background_tasks=background_tasks,
    )

    db.commit()
    db.refresh(termination_request)
    return termination_request


@router.post("/{request_id}/reject", response_model=ContractTerminationRequestSchema)
def reject_termination_request(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks,
    request_id: int,
    reason: str,
):
    """拒绝提前解约申请"""
    termination_request = crud_contract_change.get_contract_termination_request(
        db=db,
        request_id=request_id
    )

    if not termination_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提前解约申请不存在"
        )

    contract = termination_request.contract
    if current_user.id == termination_request.initiator_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="发起人不能审批自己的申请")
    if current_user.id not in [contract.tenant_id, contract.landlord_id]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权处理此申请")

    try:
        termination_request = crud_contract_change.reject_contract_termination_request(
            db=db,
            request=termination_request,
            responder_id=current_user.id,
            response_opinion=reason
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    _notify_user(
        db=db,
        from_user_id=current_user.id,
        to_user_id=termination_request.initiator_id,
        content=f"合同（编号：{contract.contract_no}）的提前解约申请已被拒绝。原因：{reason}",
        property_id=contract.property_id,
        background_tasks=background_tasks,
    )

    db.commit()
    db.refresh(termination_request)
    return termination_request