from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_active_admin, get_current_active_landlord, get_db
from app.crud import crud_audit, crud_contract
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
)
from app.core.enums import (
    ContractStatus,
    PropertyReviewStatus,
    PropertyStatus,
    CANCELLABLE_STATUSES,
    REJECTABLE_STATUSES,
)

router = APIRouter()


def _send_message_to_user(
    db: Session,
    from_user_id: int,
    to_user_id: int,
    content: str,
    property_id: Optional[int] = None,
    message_type: str = "notification",
) -> None:
    """发送系统消息给用户"""
    message = Message(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        content=content,
        property_id=property_id,
        is_read=False,
        message_type=message_type,
    )
    db.add(message)


@router.post("/", response_model=ContractSchema, status_code=status.HTTP_201_CREATED)
def create_contract(
    contract_in: ContractCreate,
    request: Request,
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
    if property_obj.status != PropertyStatus.VACANT:
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


@router.get("/", response_model=List[ContractSchema])
def list_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, description="按状态筛选"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """获取合同列表（根据角色过滤）"""
    if current_user.role == "admin":
        return crud_contract.get_contracts(db, status=status_filter, skip=skip, limit=limit)
    elif current_user.role == "landlord":
        return crud_contract.get_contracts(db, landlord_id=current_user.id, status=status_filter, skip=skip, limit=limit)
    else:
        return crud_contract.get_contracts(db, tenant_id=current_user.id, status=status_filter, skip=skip, limit=limit)


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

    # 允许在双方都未完全签署前修改
    if contract.status == ContractStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已生效的合同不能修改条款")
    if contract.status in [ContractStatus.TERMINATED, ContractStatus.CANCELLED, ContractStatus.REJECTED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已结束的合同不能修改")

    updated = crud_contract.update_contract(db, contract, contract_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_contract",
        target_type="contract",
        target_id=updated.id,
        detail=f"Contract updated (signature reset if needed)",
        ip_address=ip_address,
    )
    return updated


@router.put("/{contract_id}/sign/landlord", response_model=ContractSchema)
def sign_contract_landlord(
    contract_id: int,
    request: Request,
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
    if contract.status in [ContractStatus.CANCELLED, ContractStatus.REJECTED, ContractStatus.TERMINATED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已结束的合同不能签署")

    contract.signed_by_landlord = 1
    contract.landlord_signed_at = datetime.utcnow()

    if contract.signed_by_tenant:
        # 双方都已签署，合同生效
        contract.status = ContractStatus.ACTIVE
        property_obj = db.query(Property).filter(Property.id == contract.property_id).first()
        if property_obj:
            property_obj.status = PropertyStatus.RENTED

        # 通知租客合同已生效
        _send_message_to_user(
            db=db,
            from_user_id=current_user.id,
            to_user_id=contract.tenant_id,
            content=f"租赁合同（编号：{contract.contract_no}）已由房东签署，合同正式生效。",
            property_id=contract.property_id,
        )
    else:
        contract.status = ContractStatus.PENDING_TENANT_SIGN

        # 通知租客来签署
        _send_message_to_user(
            db=db,
            from_user_id=current_user.id,
            to_user_id=contract.tenant_id,
            content=f"房东已签署租赁合同（编号：{contract.contract_no}），请您登录系统完成签署。",
            property_id=contract.property_id,
        )

    db.commit()
    db.refresh(contract)

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="sign_contract_landlord",
        target_type="contract",
        target_id=contract.id,
        detail="Contract signed by landlord",
        ip_address=ip_address,
    )
    return contract


@router.put("/{contract_id}/sign/tenant", response_model=ContractSchema)
def sign_contract_tenant(
    contract_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """租客签署合同"""
    contract = crud_contract.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")
    if contract.tenant_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权签署此合同")
    if contract.signed_by_tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="租客已签署此合同")
    if contract.status in [ContractStatus.CANCELLED, ContractStatus.REJECTED, ContractStatus.TERMINATED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已结束的合同不能签署")

    contract.signed_by_tenant = 1
    contract.tenant_signed_at = datetime.utcnow()

    if contract.signed_by_landlord:
        # 双方都已签署，合同生效
        contract.status = ContractStatus.ACTIVE
        property_obj = db.query(Property).filter(Property.id == contract.property_id).first()
        if property_obj:
            property_obj.status = PropertyStatus.RENTED

        # 通知房东合同已生效
        _send_message_to_user(
            db=db,
            from_user_id=current_user.id,
            to_user_id=contract.landlord_id,
            content=f"租赁合同（编号：{contract.contract_no}）已由租客签署，合同正式生效。",
            property_id=contract.property_id,
        )
    else:
        contract.status = ContractStatus.PENDING_LANDLORD_SIGN

        # 通知房东来签署
        _send_message_to_user(
            db=db,
            from_user_id=current_user.id,
            to_user_id=contract.landlord_id,
            content=f"租客已签署租赁合同（编号：{contract.contract_no}），请您登录系统完成签署。",
            property_id=contract.property_id,
        )

    db.commit()
    db.refresh(contract)

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="sign_contract_tenant",
        target_type="contract",
        target_id=contract.id,
        detail="Contract signed by tenant",
        ip_address=ip_address,
    )
    return contract


@router.put("/{contract_id}/withdraw/landlord", response_model=ContractSchema)
def withdraw_signature_landlord(
    contract_id: int,
    request: Request,
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

    # 状态检查
    if contract.status not in REJECTABLE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有待签约状态的合同可以拒绝"
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

    # 合同终止，恢复房源状态为空闲
    property_obj = db.query(Property).filter(Property.id == contract.property_id).first()
    if property_obj:
        property_obj.status = PropertyStatus.VACANT

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

