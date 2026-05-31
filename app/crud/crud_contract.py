from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.models.property import Property
from app.schemas.contract import ContractCreate, ContractUpdate
from app.core.enums import (
    ContractStatus,
    PropertyStatus,
    CANCELLABLE_STATUSES,
    ACTIVE_OR_PENDING_STATUSES,
)


def _generate_contract_no() -> str:
    return f"CT{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"


def get_contract(db: Session, contract_id: int) -> Optional[Contract]:
    return db.query(Contract).filter(Contract.id == contract_id).first()


def get_contracts(
    db: Session,
    landlord_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    property_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[Contract]:
    query = db.query(Contract)
    if landlord_id is not None:
        query = query.filter(Contract.landlord_id == landlord_id)
    if tenant_id is not None:
        query = query.filter(Contract.tenant_id == tenant_id)
    if property_id is not None:
        query = query.filter(Contract.property_id == property_id)
    if status is not None:
        query = query.filter(Contract.status == status)
    return query.order_by(Contract.created_at.desc()).offset(skip).limit(limit).all()


def create_contract(db: Session, landlord_id: int, contract_in: ContractCreate) -> Contract:
    contract = Contract(
        contract_no=_generate_contract_no(),
        property_id=contract_in.property_id,
        landlord_id=landlord_id,
        tenant_id=contract_in.tenant_id,
        start_date=contract_in.start_date,
        end_date=contract_in.end_date,
        monthly_rent=contract_in.monthly_rent,
        deposit=contract_in.deposit,
        payment_day=contract_in.payment_day,
        terms=contract_in.terms,
        remark=contract_in.remark,
        status=ContractStatus.PENDING_SIGN,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


def update_contract(db: Session, db_contract: Contract, contract_in: ContractUpdate) -> Contract:
    update_data = contract_in.model_dump(exclude_unset=True)

    # 如果合同已签署，修改条款需要重置签署状态
    needs_reset_signature = False
    signature_reset_fields = ['start_date', 'end_date', 'monthly_rent', 'deposit', 'payment_day', 'terms']

    for field in signature_reset_fields:
        if field in update_data and update_data[field] != getattr(db_contract, field):
            needs_reset_signature = True
            break

    for field, value in update_data.items():
        setattr(db_contract, field, value)

    # 如果修改了关键条款且已有签署，重置签署状态
    if needs_reset_signature and (db_contract.signed_by_landlord or db_contract.signed_by_tenant):
        db_contract.signed_by_landlord = 0
        db_contract.signed_by_tenant = 0
        db_contract.landlord_signed_at = None
        db_contract.tenant_signed_at = None
        db_contract.status = ContractStatus.PENDING_SIGN

    db.commit()
    db.refresh(db_contract)
    return db_contract


def cancel_contract(db: Session, contract: Contract) -> Contract:
    """取消合同（仅未完全签署的合同可取消）"""
    contract.status = ContractStatus.CANCELLED
    db.commit()
    db.refresh(contract)
    return contract


def reject_contract(db: Session, contract: Contract, reason: Optional[str] = None) -> Contract:
    """拒绝合同"""
    contract.status = ContractStatus.REJECTED
    contract.terminate_reason = reason
    db.commit()
    db.refresh(contract)
    return contract


def withdraw_signature(db: Session, contract: Contract, user_role: str) -> Contract:
    """撤回签署（仅当双方未都签署时可撤回）"""
    # 已生效的合同不能撤回，必须使用终止申请流程
    if contract.status == ContractStatus.ACTIVE:
        raise ValueError("合同已生效，无法撤回签署，请使用终止功能")
    
    # 已终止、已取消、已过期的合同不能撤回
    if contract.status in [ContractStatus.TERMINATED, ContractStatus.CANCELLED, ContractStatus.EXPIRED]:
        raise ValueError("当前状态的合同不允许撤回签署")
    
    # 只有部分签署或待签约状态才能撤回
    if contract.status not in [ContractStatus.PART_SIGNED, ContractStatus.PENDING_SIGN]:
        raise ValueError("当前状态不允许撤回签署")

    if user_role == "landlord":
        if not contract.signed_by_landlord:
            raise ValueError("房东尚未签署此合同")
        contract.signed_by_landlord = 0
        contract.landlord_signed_at = None
        # 如果租客已签，状态变为待房东签约；否则变为待签约
        if contract.signed_by_tenant:
            contract.status = ContractStatus.PENDING_LANDLORD_SIGN
        else:
            contract.status = ContractStatus.PENDING_SIGN
            # 双方都未签署，恢复房源状态
            restore_property_status_on_cancel(db, contract.property_id)
    elif user_role == "tenant":
        if not contract.signed_by_tenant:
            raise ValueError("租客尚未签署此合同")
        contract.signed_by_tenant = 0
        contract.tenant_signed_at = None
        # 如果房东已签，状态变为待租客签约；否则变为待签约
        if contract.signed_by_landlord:
            contract.status = ContractStatus.PENDING_TENANT_SIGN
        else:
            contract.status = ContractStatus.PENDING_SIGN
            # 双方都未签署，恢复房源状态
            restore_property_status_on_cancel(db, contract.property_id)
    else:
        raise ValueError("无效的用户角色")

    db.commit()
    db.refresh(contract)
    return contract


def check_property_has_active_contract(db: Session, property_id: int, exclude_contract_id: Optional[int] = None) -> bool:
    """检查房源是否已有活跃或进行中的合同"""
    query = db.query(Contract).filter(
        Contract.property_id == property_id,
        Contract.status.in_(ACTIVE_OR_PENDING_STATUSES)
    )
    if exclude_contract_id:
        query = query.filter(Contract.id != exclude_contract_id)
    return query.first() is not None


def restore_property_status_on_cancel(db: Session, property_id: int) -> None:
    """合同取消/拒绝后，恢复房源状态为已发布（空置）"""
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    if property_obj and property_obj.status == PropertyStatus.RENTED:
        # 只有当没有其他活跃合同时才恢复状态
        if not check_property_has_active_contract(db, property_id):
            property_obj.status = PropertyStatus.PUBLISHED
            db.commit()


def sign_contract(
    db: Session,
    contract: Contract,
    user_id: int,
    user_role: str,
    signature_image: Optional[str] = None,
    ip_address: Optional[str] = None,
    device_info: Optional[str] = None
) -> Contract:
    """签署合同（房东先签，租客后签）"""
    # 验证签署权限
    if user_role == "landlord" and contract.landlord_id != user_id:
        raise ValueError("无权签署此合同")
    if user_role == "tenant" and contract.tenant_id != user_id:
        raise ValueError("无权签署此合同")
    
    # 检查合同状态
    if contract.status in [ContractStatus.CANCELLED, ContractStatus.TERMINATED, ContractStatus.EXPIRED]:
        raise ValueError("已取消、已终止或已过期的合同不能签署")
    
    # 检查是否已签署
    if user_role == "landlord" and contract.signed_by_landlord:
        raise ValueError("房东已签署此合同")
    if user_role == "tenant" and contract.signed_by_tenant:
        raise ValueError("租客已签署此合同")
    
    # 关键验证：租客只能在房东已签署的情况下才能签署
    if user_role == "tenant" and not contract.signed_by_landlord:
        raise ValueError("房东尚未签署此合同，请等待房东先签署")
    
    # 记录签署信息
    now = datetime.utcnow()
    if user_role == "landlord":
        contract.signed_by_landlord = 1
        contract.landlord_signed_at = now
        contract.landlord_sign_ip = ip_address
        contract.landlord_sign_device = device_info
        contract.landlord_signature_image = signature_image
    elif user_role == "tenant":
        contract.signed_by_tenant = 1
        contract.tenant_signed_at = now
        contract.tenant_sign_ip = ip_address
        contract.tenant_sign_device = device_info
        contract.tenant_signature_image = signature_image
    
    # 更新合同状态
    if contract.signed_by_landlord and contract.signed_by_tenant:
        # 双方都签署，合同生效
        contract.status = ContractStatus.ACTIVE
        
        # 更新房源状态为已出租
        property_obj = db.query(Property).filter(Property.id == contract.property_id).first()
        if property_obj:
            property_obj.status = PropertyStatus.RENTED
    else:
        # 只有一方签署
        contract.status = ContractStatus.PART_SIGNED
    
    db.commit()
    db.refresh(contract)
    return contract


def update_contract_editable_fields(
    db: Session,
    contract: Contract,
    update_data: dict
) -> Contract:
    """更新合同可编辑字段（仅DRAFT或PART_SIGNED且房东未签署的状态）"""
    # 将合同状态转换为字符串进行比较
    status_str = str(contract.status) if contract.status else ""
    
    # 允许编辑的状态：draft 或 part_signed且房东未签署
    if status_str == "draft":
        pass  # 允许编辑
    elif status_str == "part_signed" and not contract.signed_by_landlord:
        pass  # 允许编辑（房东未签署）
    else:
        raise ValueError("只有草稿状态或部分签署状态（房东未签署）的合同可以编辑")
    
    # 允许编辑的字段列表
    allowed_fields = [
        'start_date', 'end_date', 'monthly_rent', 'deposit', 'payment_method',
        'payment_day', 'min_lease_term', 'renewal_notice_days', 'check_in_time',
        'allow_pets', 'early_termination_days', 'property_fee_bearer',
        'utility_fee_bearer', 'other_fee_bearer', 'additional_terms', 'remark'
    ]
    
    for field, value in update_data.items():
        if field in allowed_fields and hasattr(contract, field):
            setattr(contract, field, value)
        # 特殊处理：允许将状态从draft改为pending_sign
        elif field == 'status' and value == 'pending_sign':
            contract.status = ContractStatus.PENDING_SIGN
    
    db.commit()
    db.refresh(contract)
    return contract


def cancel_contract_by_user(
    db: Session,
    contract: Contract,
    user_id: int
) -> Contract:
    """用户取消合同（仅DRAFT或PENDING_SIGN状态）"""
    if contract.status not in CANCELLABLE_STATUSES:
        raise ValueError("当前状态不允许取消")
    
    # 验证权限（只能是房东或租客）
    if contract.landlord_id != user_id and contract.tenant_id != user_id:
        raise ValueError("无权取消此合同")
    
    contract.status = ContractStatus.CANCELLED
    contract.cancelled_at = datetime.utcnow()
    
    # 恢复房源状态
    restore_property_status_on_cancel(db, contract.property_id)
    
    db.commit()
    db.refresh(contract)
    return contract


def check_and_expire_contracts(db: Session) -> int:
    """检查并过期已到期的合同"""
    now = datetime.utcnow()
    expired_contracts = db.query(Contract).filter(
        Contract.status == ContractStatus.ACTIVE,
        Contract.end_date < now
    ).all()
    
    count = 0
    for contract in expired_contracts:
        contract.status = ContractStatus.EXPIRED
        # 恢复房源状态为已发布（空置）
        property_obj = db.query(Property).filter(Property.id == contract.property_id).first()
        if property_obj and property_obj.status == PropertyStatus.RENTED:
            property_obj.status = PropertyStatus.PUBLISHED
        count += 1
    
    if count > 0:
        db.commit()
    
    return count
