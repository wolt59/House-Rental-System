from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.contract_change_request import ContractChangeRequest
from app.models.contract_termination_request import ContractTerminationRequest
from app.models.contract import Contract
from app.models.property import Property
from app.schemas.contract_change_request import ContractChangeRequestCreate
from app.schemas.contract_termination_request import ContractTerminationRequestCreate
from app.core.enums import ContractStatus, PropertyStatus


# ==================== 合同变更 CRUD ====================

def get_contract_change_request(db: Session, request_id: int) -> Optional[ContractChangeRequest]:
    """获取单个合同变更申请"""
    return db.query(ContractChangeRequest).filter(ContractChangeRequest.id == request_id).first()


def get_contract_change_requests(
    db: Session,
    contract_id: Optional[int] = None,
    initiator_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[ContractChangeRequest]:
    """获取合同变更申请列表"""
    query = db.query(ContractChangeRequest)
    
    if contract_id is not None:
        query = query.filter(ContractChangeRequest.contract_id == contract_id)
    if initiator_id is not None:
        query = query.filter(ContractChangeRequest.initiator_id == initiator_id)
    if status is not None:
        query = query.filter(ContractChangeRequest.status == status)
    
    return query.order_by(ContractChangeRequest.created_at.desc()).offset(skip).limit(limit).all()


def create_contract_change_request(
    db: Session,
    initiator_id: int,
    request_in: ContractChangeRequestCreate
) -> ContractChangeRequest:
    """创建合同变更申请"""
    # 验证合同是否存在
    contract = db.query(Contract).filter(Contract.id == request_in.contract_id).first()
    if not contract:
        raise ValueError("合同不存在")
    
    # 验证合同状态必须是ACTIVE
    if contract.status != ContractStatus.ACTIVE:
        raise ValueError("只有生效中的合同才能发起变更申请")
    
    # 验证发起人必须是合同的房东或租客
    if contract.landlord_id != initiator_id and contract.tenant_id != initiator_id:
        raise ValueError("无权为此合同发起变更申请")
    
    # 检查是否已有待处理的变更申请
    existing_request = db.query(ContractChangeRequest).filter(
        ContractChangeRequest.contract_id == request_in.contract_id,
        ContractChangeRequest.status == "pending"
    ).first()
    
    if existing_request:
        raise ValueError("该合同已有待处理的变更申请")
    
    # 验证变更字段是否在允许范围内
    allowed_fields = [
        'end_date', 'monthly_rent', 'payment_method', 
        'property_fee_bearer', 'utility_fee_bearer', 
        'other_fee_bearer', 'allow_pets', 'additional_terms'
    ]
    
    for change_field in request_in.change_fields:
        if change_field.field not in allowed_fields:
            raise ValueError(f"字段 {change_field.field} 不允许变更")
    
    # 创建变更申请
    change_request = ContractChangeRequest(
        contract_id=request_in.contract_id,
        initiator_id=initiator_id,
        change_reason=request_in.change_reason,
        change_fields=[field.dict() for field in request_in.change_fields],
        status="pending",
    )
    
    # 更新合同状态为变更协商中
    contract.status = ContractStatus.CHANGE_NEGOTIATING
    
    db.add(change_request)
    db.commit()
    db.refresh(change_request)
    return change_request


def approve_contract_change_request(
    db: Session,
    request: ContractChangeRequest,
    responder_id: int,
    response_opinion: Optional[str] = None
) -> ContractChangeRequest:
    """同意合同变更申请"""
    contract = db.query(Contract).filter(Contract.id == request.contract_id).first()
    if not contract:
        raise ValueError("合同不存在")
    
    # 验证响应人必须是合同的另一方
    if contract.landlord_id != responder_id and contract.tenant_id != responder_id:
        raise ValueError("无权处理此变更申请")
    
    if request.initiator_id == responder_id:
        raise ValueError("不能响应自己发起的申请")
    
    if request.status != "pending":
        raise ValueError("申请状态不正确")
    
    # 应用变更到合同
    for change_field in request.change_fields:
        field_name = change_field['field']
        new_value = change_field['new_value']
        
        if hasattr(contract, field_name):
            setattr(contract, field_name, new_value)
    
    # 更新申请状态
    request.status = "approved"
    request.responder_id = responder_id
    request.response_opinion = response_opinion
    request.responded_at = datetime.utcnow()
    
    # 恢复合同状态为ACTIVE
    contract.status = ContractStatus.ACTIVE
    
    db.commit()
    db.refresh(request)
    return request


def reject_contract_change_request(
    db: Session,
    request: ContractChangeRequest,
    responder_id: int,
    response_opinion: str
) -> ContractChangeRequest:
    """拒绝合同变更申请"""
    contract = db.query(Contract).filter(Contract.id == request.contract_id).first()
    if not contract:
        raise ValueError("合同不存在")
    
    # 验证响应人必须是合同的另一方
    if contract.landlord_id != responder_id and contract.tenant_id != responder_id:
        raise ValueError("无权处理此变更申请")
    
    if request.initiator_id == responder_id:
        raise ValueError("不能响应自己发起的申请")
    
    if request.status != "pending":
        raise ValueError("申请状态不正确")
    
    # 更新申请状态
    request.status = "rejected"
    request.responder_id = responder_id
    request.response_opinion = response_opinion
    request.responded_at = datetime.utcnow()
    
    # 恢复合同状态为ACTIVE
    contract.status = ContractStatus.ACTIVE
    
    db.commit()
    db.refresh(request)
    return request


# ==================== 提前解约 CRUD ====================

def get_contract_termination_request(db: Session, request_id: int) -> Optional[ContractTerminationRequest]:
    """获取单个提前解约申请"""
    return db.query(ContractTerminationRequest).filter(ContractTerminationRequest.id == request_id).first()


def get_contract_termination_requests(
    db: Session,
    contract_id: Optional[int] = None,
    initiator_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[ContractTerminationRequest]:
    """获取提前解约申请列表"""
    query = db.query(ContractTerminationRequest)
    
    if contract_id is not None:
        query = query.filter(ContractTerminationRequest.contract_id == contract_id)
    if initiator_id is not None:
        query = query.filter(ContractTerminationRequest.initiator_id == initiator_id)
    if status is not None:
        query = query.filter(ContractTerminationRequest.status == status)
    
    return query.order_by(ContractTerminationRequest.created_at.desc()).offset(skip).limit(limit).all()


def get_contract_termination_requests_by_role(
    db: Session,
    landlord_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    contract_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[ContractTerminationRequest]:
    """根据用户角色获取提前解约申请列表（房东或租客）"""
    # 先获取用户的合同列表
    if landlord_id is not None:
        user_contracts = db.query(Contract).filter(Contract.landlord_id == landlord_id).all()
    elif tenant_id is not None:
        user_contracts = db.query(Contract).filter(Contract.tenant_id == tenant_id).all()
    else:
        user_contracts = []
    
    if not user_contracts:
        return []
    
    contract_ids = [c.id for c in user_contracts]
    
    # 查询这些合同的解约申请
    query = db.query(ContractTerminationRequest).filter(
        ContractTerminationRequest.contract_id.in_(contract_ids)
    )
    
    if contract_id is not None:
        query = query.filter(ContractTerminationRequest.contract_id == contract_id)
    if status is not None:
        query = query.filter(ContractTerminationRequest.status == status)
    
    return query.order_by(ContractTerminationRequest.created_at.desc()).offset(skip).limit(limit).all()


def create_contract_termination_request(
    db: Session,
    initiator_id: int,
    request_in: ContractTerminationRequestCreate
) -> ContractTerminationRequest:
    """创建提前解约申请"""
    # 验证合同是否存在
    contract = db.query(Contract).filter(Contract.id == request_in.contract_id).first()
    if not contract:
        raise ValueError("合同不存在")
    
    # 验证合同状态必须是ACTIVE
    if contract.status != ContractStatus.ACTIVE:
        raise ValueError("只有生效中的合同才能发起提前解约申请")
    
    # 验证发起人必须是合同的房东或租客
    if contract.landlord_id != initiator_id and contract.tenant_id != initiator_id:
        raise ValueError("无权为此合同发起解约申请")
    
    # 检查是否已有待处理的解约申请
    existing_request = db.query(ContractTerminationRequest).filter(
        ContractTerminationRequest.contract_id == request_in.contract_id,
        ContractTerminationRequest.status == "pending"
    ).first()
    
    if existing_request:
        raise ValueError("该合同已有待处理的解约申请")
    
    # 创建解约申请
    termination_request = ContractTerminationRequest(
        contract_id=request_in.contract_id,
        initiator_id=initiator_id,
        termination_reason=request_in.termination_reason,
        expected_termination_date=request_in.expected_termination_date,
        penalty_amount=request_in.penalty_amount,
        deposit_handling=request_in.deposit_handling,
        additional_notes=request_in.additional_notes,
        status="pending",
    )
    
    # 更新合同状态为解约协商中
    contract.status = ContractStatus.TERMINATE_NEGOTIATING
    
    db.add(termination_request)
    db.commit()
    db.refresh(termination_request)
    return termination_request


def approve_contract_termination_request(
    db: Session,
    request: ContractTerminationRequest,
    responder_id: int,
    response_opinion: Optional[str] = None
) -> ContractTerminationRequest:
    """同意提前解约申请"""
    contract = db.query(Contract).filter(Contract.id == request.contract_id).first()
    if not contract:
        raise ValueError("合同不存在")
    
    # 验证响应人必须是合同的另一方
    if contract.landlord_id != responder_id and contract.tenant_id != responder_id:
        raise ValueError("无权处理此解约申请")
    
    if request.initiator_id == responder_id:
        raise ValueError("不能响应自己发起的申请")
    
    if request.status != "pending":
        raise ValueError("申请状态不正确")
    
    # 更新合同状态为已终止
    contract.status = ContractStatus.TERMINATED
    contract.terminated_at = datetime.utcnow()
    contract.terminate_reason = f"双方协商一致提前解约：{request.termination_reason}"
    
    # 恢复房源状态为已发布（空置）
    property_obj = db.query(Property).filter(Property.id == contract.property_id).first()
    if property_obj and property_obj.status == PropertyStatus.RENTED:
        property_obj.status = PropertyStatus.PUBLISHED
    
    # 更新申请状态
    request.status = "approved"
    request.responder_id = responder_id
    request.response_opinion = response_opinion
    request.responded_at = datetime.utcnow()
    
    db.commit()
    db.refresh(request)
    return request


def reject_contract_termination_request(
    db: Session,
    request: ContractTerminationRequest,
    responder_id: int,
    response_opinion: str
) -> ContractTerminationRequest:
    """拒绝提前解约申请"""
    contract = db.query(Contract).filter(Contract.id == request.contract_id).first()
    if not contract:
        raise ValueError("合同不存在")
    
    # 验证响应人必须是合同的另一方
    if contract.landlord_id != responder_id and contract.tenant_id != responder_id:
        raise ValueError("无权处理此解约申请")
    
    if request.initiator_id == responder_id:
        raise ValueError("不能响应自己发起的申请")
    
    if request.status != "pending":
        raise ValueError("申请状态不正确")
    
    # 恢复合同状态为ACTIVE
    contract.status = ContractStatus.ACTIVE
    
    # 更新申请状态
    request.status = "rejected"
    request.responder_id = responder_id
    request.response_opinion = response_opinion
    request.responded_at = datetime.utcnow()
    
    db.commit()
    db.refresh(request)
    return request
