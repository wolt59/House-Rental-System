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
    REJECTABLE_STATUSES,
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
    if contract.status == ContractStatus.ACTIVE:
        raise ValueError("合同已生效，无法撤回签署，请使用终止功能")

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
    """合同取消/拒绝后，恢复房源状态为空闲"""
    property_obj = db.query(Property).filter(Property.id == property_id).first()
    if property_obj and property_obj.status == PropertyStatus.RENTED:
        # 只有当没有其他活跃合同时才恢复状态
        if not check_property_has_active_contract(db, property_id):
            property_obj.status = PropertyStatus.VACANT
            db.commit()
