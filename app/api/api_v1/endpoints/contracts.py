from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_active_admin, get_current_active_landlord, get_db
from app.crud import crud_audit, crud_contract, crud_message, crud_payment
from app.schemas.common import PaginatedResponse
from app.models.contract import Contract
from app.models.property import Property
from app.models.message import Message
from app.schemas.contract import (
    Contract as ContractSchema,
    ContractCreate,
    ContractAutoCreate,
    ContractUpdate,
    ContractReject,
    ContractTerminate,
    ContractSignRequest,
)
from app.core.enums import (
    ContractStatus,
    PropertyReviewStatus,
    PropertyStatus,
    CANCELLABLE_STATUSES,
    MessageType,
)
from app.api.websocket import ws_manager

router = APIRouter()


def _send_message_to_user(
    db: Session,
    from_user_id: int,
    to_user_id: int,
    content: str,
    property_id: Optional[int] = None,
    message_type: str = MessageType.NOTIFICATION.value,
    background_tasks: Optional[BackgroundTasks] = None,
) -> None:
    """发送系统消息给用户（含 WebSocket 实时推送）"""
    message = Message(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        content=content,
        property_id=property_id,
        is_read=False,
        message_type=message_type,
    )
    db.add(message)
    db.flush()
    db.refresh(message)

    if background_tasks:
        unread_before = crud_message.get_unread_count(db, user_id=to_user_id, message_type="notification")

        async def notify_user():
            payload = {
                "type": "new_message",
                "message": {
                    "id": message.id,
                    "from_user_id": message.from_user_id,
                    "to_user_id": message.to_user_id,
                    "content": message.content,
                    "message_type": message.message_type,
                    "property_id": message.property_id,
                    "is_read": message.is_read,
                    "created_at": message.created_at.isoformat() if message.created_at else None,
                },
                "unread_count": unread_before + 1,
            }
            await ws_manager.send_personal(payload, to_user_id)

        background_tasks.add_task(notify_user)


@router.post("/", response_model=ContractSchema, status_code=status.HTTP_201_CREATED)
def create_contract(
    contract_in: ContractCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_landlord),
):
    """房东创建合同"""
    property_obj = db.query(Property).filter(Property.id == contract_in.property_id).first()
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="房源不存在")
    if property_obj.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权为此房源创建合同")
    if property_obj.review_status != PropertyReviewStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="房源必须审核通过后才能创建合同")

    # 检查房源是否已有活跃合同
    if crud_contract.check_property_has_active_contract(db, contract_in.property_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该房源已有进行中的合同"
        )

    contract = crud_contract.create_contract(db, landlord_id=current_user.id, contract_in=contract_in)

    # 发送消息通知租客
    _send_message_to_user(
        db=db,
        from_user_id=current_user.id,
        to_user_id=contract_in.tenant_id,
        content=f"房东为您创建了新的租赁合同（编号：{contract.contract_no}），请登录系统查看并签署。",
        property_id=contract_in.property_id,
        background_tasks=background_tasks,
    )
    db.commit()

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="create_contract",
        target_type="contract",
        target_id=contract.id,
        detail=f"Contract created for property {contract.property_id}",
        ip_address=ip_address,
    )
    return contract


@router.post("/auto-create", response_model=ContractSchema, status_code=status.HTTP_201_CREATED)
def auto_create_contract(
    contract_in: ContractAutoCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """租客申请签约（自动创建合同）"""
    if current_user.role != "tenant":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅租客可以申请签约")

    property_obj = db.query(Property).filter(Property.id == contract_in.property_id).first()
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="房源不存在")
    if property_obj.owner_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能租赁自己的房源")
    if property_obj.review_status != PropertyReviewStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="房源未通过审核")
    if property_obj.status != PropertyStatus.PUBLISHED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="房源当前不可租赁")

    # 检查房源是否已有活跃合同
    if crud_contract.check_property_has_active_contract(db, contract_in.property_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该房源已有进行中的合同")

    now = datetime.utcnow()
    contract = Contract(
        contract_no=f"CT{now.strftime('%Y%m%d%H%M%S%f')}",
        property_id=contract_in.property_id,
        landlord_id=property_obj.owner_id,
        tenant_id=current_user.id,
        start_date=contract_in.start_date or now,
        end_date=contract_in.end_date or (now.replace(year=now.year + 1)),
        monthly_rent=property_obj.rent,
        deposit=contract_in.deposit if contract_in.deposit is not None else property_obj.deposit,
        payment_day=contract_in.payment_day if contract_in.payment_day is not None else 1,
        terms=contract_in.terms,
        status=ContractStatus.PENDING_SIGN,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)

    # 发送消息通知房东
    _send_message_to_user(
        db=db,
        from_user_id=current_user.id,
        to_user_id=property_obj.owner_id,
        content=f"租客申请签约您的房源（{property_obj.title}），请登录系统查看并处理。",
        property_id=contract_in.property_id,
        background_tasks=background_tasks,
    )
    db.commit()

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="create_contract",
        target_type="contract",
        target_id=contract.id,
        detail=f"Contract auto-created by tenant for property {contract.property_id}",
        ip_address=ip_address,
    )
    return contract


@router.get("/")
def list_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, description="按状态筛选"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """获取合同列表（根据角色过滤）"""
    # 自动检查并过期已到期的合同
    try:
        expired_count = crud_contract.check_and_expire_contracts(db)
        if expired_count > 0:
            print(f"自动过期了 {expired_count} 个合同")
    except Exception as e:
        print(f"检查过期合同时出错: {e}")

    if current_user.role == "admin":
        items = crud_contract.get_contracts(db, status=status_filter, skip=skip, limit=limit)
        total = crud_contract.count_contracts(db, status=status_filter)
    elif current_user.role == "landlord":
        items = crud_contract.get_contracts(db, landlord_id=current_user.id, status=status_filter, skip=skip, limit=limit)
        total = crud_contract.count_contracts(db, landlord_id=current_user.id, status=status_filter)
    else:
        items = crud_contract.get_contracts(db, tenant_id=current_user.id, status=status_filter, skip=skip, limit=limit)
        total = crud_contract.count_contracts(db, tenant_id=current_user.id, status=status_filter)
    return {"items": items, "total": total}


@router.get("/{contract_id}", response_model=ContractSchema)
def read_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """获取合同详情"""
    contract = crud_contract.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")
    if current_user.role != "admin" and contract.landlord_id != current_user.id and contract.tenant_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看此合同")
    return contract


@router.put("/{contract_id}", response_model=ContractSchema)
def update_contract(
    contract_id: int,
    contract_in: ContractUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """更新合同（仅双方都未签署前可修改）"""
    contract = crud_contract.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")
    if contract.landlord_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改此合同")

    # 将合同状态转换为字符串进行比较
    status_str = str(contract.status) if contract.status else ""

    # 允许在双方都未完全签署前修改
    if status_str == "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已生效的合同不能修改条款")
    if status_str in ["terminated", "cancelled", "rejected"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已结束的合同不能修改")

    # 对于DRAFT、PENDING_SIGN、PENDING_LANDLORD_SIGN、PENDING_TENANT_SIGN、PART_SIGNED状态，使用简化的更新方法
    if status_str in ["draft", "pending_sign", "pending_landlord_sign", "pending_tenant_sign", "part_signed"]:
        update_data = contract_in.model_dump(exclude_unset=True)
        try:
            updated = crud_contract.update_contract_editable_fields(db, contract, update_data)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        # 其他状态使用原有的更新方法（可能重置签署状态）
        updated = crud_contract.update_contract(db, contract, contract_in)
    
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_contract",
        target_type="contract",
        target_id=updated.id,
        detail=f"Contract updated (status: {updated.status})",
        ip_address=ip_address,
    )
    return updated


@router.put("/{contract_id}/sign/landlord", response_model=ContractSchema)
def sign_contract_landlord(
    contract_id: int,
    sign_request: ContractSignRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_landlord),
):
    """房东签署合同"""
    contract = crud_contract.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")
    if contract.landlord_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权签署此合同")
    if contract.signed_by_landlord:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="房东已签署此合同")
    # 只有草稿状态的合同才能由房东签署
    if contract.status != ContractStatus.DRAFT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只有草稿状态的合同可以签署")

    # 记录签署信息（包括手写签名）
    device_info = sign_request.device_info
    signature_image = sign_request.signature_image
    
    contract.signed_by_landlord = 1
    contract.landlord_signed_at = datetime.utcnow()
    contract.landlord_sign_ip = None  # 不记录IP地址
    contract.landlord_sign_device = device_info
    contract.landlord_signature_image = signature_image

    if contract.signed_by_tenant:
        # 双方都已签署，合同生效
        contract.status = ContractStatus.ACTIVE
        property_obj = db.query(Property).filter(Property.id == contract.property_id).first()
        if property_obj:
            property_obj.status = PropertyStatus.RENTED

        # 自动生成押金和租金账单
        try:
            crud_payment.generate_bills_for_contract(db, contract)
        except Exception as e:
            print(f"生成账单失败: {e}")

        # 通知租客合同已生效
        _send_message_to_user(
            db=db,
            from_user_id=current_user.id,
            to_user_id=contract.tenant_id,
            content=f"租赁合同（编号：{contract.contract_no}）已由房东签署，合同正式生效。",
            property_id=contract.property_id,
            background_tasks=background_tasks,
        )
    else:
        # 房东已签署，等待租客签署
        contract.status = ContractStatus.PENDING_SIGN

        # 通知租客来签署
        _send_message_to_user(
            db=db,
            from_user_id=current_user.id,
            to_user_id=contract.tenant_id,
            content=f"房东已签署租赁合同（编号：{contract.contract_no}），请您登录系统完成签署。",
            property_id=contract.property_id,
            background_tasks=background_tasks,
        )

    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="sign_contract_landlord",
        target_type="contract",
        target_id=contract.id,
        detail="Contract signed by landlord",
        ip_address=None,
    )
    db.commit()
    db.refresh(contract)

    # 合同生效后独立生成账单（失败不影响合同签署）
    if contract.signed_by_tenant and contract.signed_by_landlord:
        try:
            crud_payment.generate_bills_for_contract(db, contract)
        except Exception as e:
            db.rollback()
            print(f"生成账单失败（不影响合同生效）: {e}")

    return contract


@router.put("/{contract_id}/sign/tenant", response_model=ContractSchema)
def sign_contract_tenant(
    contract_id: int,
    sign_request: ContractSignRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """租客签署合同（必须房东先签署后才能签署）"""
    contract = crud_contract.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")
    if contract.tenant_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权签署此合同")
    if contract.signed_by_tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="租客已签署此合同")
    
    # 关键验证：租客只能在房东已签署的情况下才能签署
    if not contract.signed_by_landlord:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="房东尚未签署此合同，请等待房东先签署"
        )
    
    # 只有待签署（房东已签）状态的合同租客才能签署
    if contract.status != ContractStatus.PENDING_SIGN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="当前状态不允许签署，只有待签署状态的合同可以签署"
        )

    # 记录签署信息（包括手写签名）
    device_info = sign_request.device_info
    signature_image = sign_request.signature_image
    
    contract.signed_by_tenant = 1
    contract.tenant_signed_at = datetime.utcnow()
    contract.tenant_sign_ip = None  # 不记录IP地址
    contract.tenant_sign_device = device_info
    contract.tenant_signature_image = signature_image

    # 房东已签署，租客签署后合同生效
    contract.status = ContractStatus.ACTIVE
    property_obj = db.query(Property).filter(Property.id == contract.property_id).first()
    if property_obj:
        property_obj.status = PropertyStatus.RENTED

    # 自动生成押金和租金账单
    try:
        crud_payment.generate_bills_for_contract(db, contract)
    except Exception as e:
        print(f"生成账单失败: {e}")

    # 通知房东合同已生效
    _send_message_to_user(
        db=db,
        from_user_id=current_user.id,
        to_user_id=contract.landlord_id,
        content=f"租赁合同（编号：{contract.contract_no}）已由租客签署，合同正式生效。",
        property_id=contract.property_id,
        background_tasks=background_tasks,
    )

    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="sign_contract_tenant",
        target_type="contract",
        target_id=contract.id,
        detail="Contract signed by tenant",
        ip_address=None,
    )
    db.commit()
    db.refresh(contract)

    # 合同生效后独立生成账单（失败不影响合同签署）
    if contract.signed_by_tenant and contract.signed_by_landlord:
        try:
            crud_payment.generate_bills_for_contract(db, contract)
        except Exception as e:
            db.rollback()
            print(f"生成账单失败（不影响合同生效）: {e}")

    return contract


@router.put("/{contract_id}/withdraw/landlord", response_model=ContractSchema)
def withdraw_signature_landlord(
    contract_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_landlord),
):
    """房东撤回签署"""
    contract = crud_contract.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")
    if contract.landlord_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此合同")
    if contract.status == ContractStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="合同已生效，无法撤回签署，请使用终止功能")
    if not contract.signed_by_landlord:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="房东尚未签署此合同")

    try:
        contract = crud_contract.withdraw_signature(db, contract, "landlord")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    _send_message_to_user(
        db=db,
        from_user_id=current_user.id,
        to_user_id=contract.tenant_id,
        content=f"房东已撤回对租赁合同（编号：{contract.contract_no}）的签署。",
        property_id=contract.property_id,
        background_tasks=background_tasks,
    )

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="withdraw_signature_landlord",
        target_type="contract",
        target_id=contract.id,
        detail="Landlord withdrew signature",
        ip_address=ip_address,
    )
    return contract


@router.put("/{contract_id}/withdraw/tenant", response_model=ContractSchema)
def withdraw_signature_tenant(
    contract_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """租客撤回签署"""
    contract = crud_contract.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")
    if contract.tenant_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此合同")
    if contract.status == ContractStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="合同已生效，无法撤回签署，请使用终止功能")
    if not contract.signed_by_tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="租客尚未签署此合同")

    try:
        contract = crud_contract.withdraw_signature(db, contract, "tenant")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    _send_message_to_user(
        db=db,
        from_user_id=current_user.id,
        to_user_id=contract.landlord_id,
        content=f"租客已撤回对租赁合同（编号：{contract.contract_no}）的签署。",
        property_id=contract.property_id,
        background_tasks=background_tasks,
    )

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="withdraw_signature_tenant",
        target_type="contract",
        target_id=contract.id,
        detail="Tenant withdrew signature",
        ip_address=ip_address,
    )
    return contract


@router.put("/{contract_id}/cancel", response_model=ContractSchema)
def cancel_contract(
    contract_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """取消合同（仅未完全签署的合同可取消）"""
    contract = crud_contract.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")

    # 权限检查：只有房东或租客可以取消
    if contract.landlord_id != current_user.id and contract.tenant_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此合同")

    # 状态检查：只有未完全签署的合同可以取消
    if contract.status not in CANCELLABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待签约状态的合同可以取消"
        )

    contract = crud_contract.cancel_contract(db, contract)

    # 恢复房源状态
    crud_contract.restore_property_status_on_cancel(db, contract.property_id)

    # 通知对方
    if current_user.id == contract.landlord_id:
        notify_user_id = contract.tenant_id
    else:
        notify_user_id = contract.landlord_id

    _send_message_to_user(
        db=db,
        from_user_id=current_user.id,
        to_user_id=notify_user_id,
        content=f"租赁合同（编号：{contract.contract_no}）已被取消。",
        property_id=contract.property_id,
        background_tasks=background_tasks,
    )
    db.commit()

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="cancel_contract",
        target_type="contract",
        target_id=contract.id,
        detail="Contract cancelled",
        ip_address=ip_address,
    )
    return contract


@router.put("/{contract_id}/reject", response_model=ContractSchema)
def reject_contract(
    contract_id: int,
    reject_data: ContractReject,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """拒绝合同（仅待签约状态可拒绝）"""
    contract = crud_contract.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")

    # 权限检查：只有房东或租客可以拒绝
    if contract.landlord_id != current_user.id and contract.tenant_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此合同")

    # 状态检查：只有草稿或待签署状态可以拒绝
    if contract.status not in CANCELLABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有草稿或待签署状态的合同可以拒绝"
        )

    contract = crud_contract.reject_contract(db, contract, reason=reject_data.reason)

    # 恢复房源状态
    crud_contract.restore_property_status_on_cancel(db, contract.property_id)

    # 通知对方
    if current_user.id == contract.landlord_id:
        notify_user_id = contract.tenant_id
    else:
        notify_user_id = contract.landlord_id

    _send_message_to_user(
        db=db,
        from_user_id=current_user.id,
        to_user_id=notify_user_id,
        content=f"租赁合同（编号：{contract.contract_no}）已被拒绝。原因：{reject_data.reason or '未说明'}",
        property_id=contract.property_id,
        background_tasks=background_tasks,
    )
    db.commit()

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="reject_contract",
        target_type="contract",
        target_id=contract.id,
        detail=f"Contract rejected: {reject_data.reason}",
        ip_address=ip_address,
    )
    return contract


@router.put("/{contract_id}/terminate", response_model=ContractSchema)
def terminate_contract(
    contract_id: int,
    terminate_data: ContractTerminate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """终止合同（仅生效中的合同可终止）"""
    contract = crud_contract.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")
    if contract.landlord_id != current_user.id and contract.tenant_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此合同")
    if contract.status != ContractStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只有生效中的合同可以终止")

    contract.status = ContractStatus.TERMINATED
    contract.terminated_at = datetime.utcnow()
    contract.terminate_reason = terminate_data.reason

    # 合同终止，恢复房源状态为已发布（空置）
    property_obj = db.query(Property).filter(Property.id == contract.property_id).first()
    if property_obj:
        property_obj.status = PropertyStatus.PUBLISHED

    # 取消该合同未完成的账单
    try:
        crud_payment.cancel_bills_for_contract(db, contract.id)
    except Exception as e:
        print(f"取消账单失败: {e}")

    # 通知对方
    if current_user.id == contract.landlord_id:
        notify_user_id = contract.tenant_id
    else:
        notify_user_id = contract.landlord_id

    _send_message_to_user(
        db=db,
        from_user_id=current_user.id,
        to_user_id=notify_user_id,
        content=f"租赁合同（编号：{contract.contract_no}）已终止。原因：{terminate_data.reason or '未说明'}",
        property_id=contract.property_id,
        background_tasks=background_tasks,
    )
    db.commit()
    db.refresh(contract)

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="terminate_contract",
        target_type="contract",
        target_id=contract.id,
        detail=f"Contract terminated: {terminate_data.reason}",
        ip_address=ip_address,
    )
    return contract

