from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.contract_application import ContractApplication
from app.models.booking import Booking
from app.models.property import Property
from app.models.contract import Contract
from app.schemas.contract_application import ContractApplicationCreate
from app.core.enums import BookingStatus, ContractApplicationStatus, ContractStatus, PropertyStatus


def get_contract_application(db: Session, application_id: int) -> Optional[ContractApplication]:
    """获取单个合约申请"""
    return db.query(ContractApplication).filter(ContractApplication.id == application_id).first()


def get_contract_applications(
    db: Session,
    tenant_id: Optional[int] = None,
    landlord_id: Optional[int] = None,
    property_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[ContractApplication]:
    """获取合约申请列表"""
    query = db.query(ContractApplication)
    
    if tenant_id is not None:
        query = query.filter(ContractApplication.tenant_id == tenant_id)
    if landlord_id is not None:
        query = query.filter(ContractApplication.landlord_id == landlord_id)
    if property_id is not None:
        query = query.filter(ContractApplication.property_id == property_id)
    if status is not None:
        query = query.filter(ContractApplication.status == status)
    
    return query.order_by(ContractApplication.created_at.desc()).offset(skip).limit(limit).all()


def create_contract_application(
    db: Session, 
    tenant_id: int, 
    application_in: ContractApplicationCreate
) -> ContractApplication:
    """创建合约申请"""
    # 验证看房记录是否存在且属于该租客
    booking = db.query(Booking).filter(
        Booking.id == application_in.booking_id,
        Booking.tenant_id == tenant_id
    ).first()
    
    if not booking:
        raise ValueError("看房记录不存在或无权访问")
    
    # 验证看房状态必须是completed
    if booking.status != BookingStatus.COMPLETED:
        raise ValueError("只有看房完成的预约才能发起合约申请")
    
    # 获取房源信息，确认房东ID
    property_obj = db.query(Property).filter(Property.id == booking.property_id).first()
    if not property_obj:
        raise ValueError("房源不存在")
    
    # 检查该看房记录是否已有合约申请
    existing_application = db.query(ContractApplication).filter(
        ContractApplication.booking_id == application_in.booking_id
    ).first()
    
    if existing_application:
        # 如果申请状态是已完成（已生成合同），允许再次申请
        if existing_application.status in [
            ContractApplicationStatus.APPLY_PENDING,
            ContractApplicationStatus.APPLY_APPROVED
        ]:
            raise ValueError("该看房记录已有待处理或已同意的合约申请，请等待处理完成")
    
    # 检查房源是否已有活跃合同（排除已拒绝、已取消的合同）
    active_contract = db.query(Contract).filter(
        Contract.property_id == booking.property_id,
        Contract.status.in_([
            ContractStatus.PART_SIGNED,
            ContractStatus.ACTIVE
        ])
    ).first()
    
    if active_contract:
        raise ValueError("该房源已有进行中的合同")
    
    # 创建合约申请
    application = ContractApplication(
        booking_id=application_in.booking_id,
        property_id=booking.property_id,
        tenant_id=tenant_id,
        landlord_id=property_obj.owner_id,
        start_date=application_in.start_date,
        end_date=application_in.end_date,
        payment_method=application_in.payment_method,
        additional_notes=application_in.additional_notes,
        status=ContractApplicationStatus.APPLY_PENDING,
    )
    
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def approve_contract_application(
    db: Session,
    application: ContractApplication,
    landlord_id: int,
    response: Optional[str] = None
) -> ContractApplication:
    """房东同意合约申请，生成合同草稿"""
    if application.landlord_id != landlord_id:
        raise ValueError("无权处理此申请")
    
    if application.status != ContractApplicationStatus.APPLY_PENDING:
        raise ValueError("申请状态不正确")
    
    # 生成合同草稿
    contract = Contract(
        contract_no=f"CT{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
        property_id=application.property_id,
        landlord_id=application.landlord_id,
        tenant_id=application.tenant_id,
        start_date=application.start_date,
        end_date=application.end_date,
        monthly_rent=0,  # 需要后续填写
        deposit=0,  # 需要后续填写
        payment_method=application.payment_method,
        status=ContractStatus.DRAFT,
    )
    
    db.add(contract)
    db.flush()  # 获取contract.id
    
    # 更新申请状态
    application.status = ContractApplicationStatus.APPLY_APPROVED
    application.contract_id = contract.id
    application.landlord_response = response
    application.responded_at = datetime.utcnow()
    
    db.commit()
    db.refresh(application)
    return application


def reject_contract_application(
    db: Session,
    application: ContractApplication,
    landlord_id: int,
    reason: str
) -> ContractApplication:
    """房东拒绝合约申请"""
    if application.landlord_id != landlord_id:
        raise ValueError("无权处理此申请")
    
    if application.status != ContractApplicationStatus.APPLY_PENDING:
        raise ValueError("申请状态不正确")
    
    application.status = ContractApplicationStatus.APPLY_REJECTED
    application.landlord_response = reason
    application.responded_at = datetime.utcnow()
    
    db.commit()
    db.refresh(application)
    return application


def cancel_contract_application(
    db: Session,
    application: ContractApplication,
    tenant_id: int
) -> ContractApplication:
    """租客取消合约申请"""
    if application.tenant_id != tenant_id:
        raise ValueError("无权取消此申请")
    
    if application.status != ContractApplicationStatus.APPLY_PENDING:
        raise ValueError("只能取消待处理的申请")
    
    application.status = ContractApplicationStatus.APPLY_CANCELLED
    application.cancelled_at = datetime.utcnow()
    
    db.commit()
    db.refresh(application)
    return application


def check_booking_has_pending_application(db: Session, booking_id: int) -> bool:
    """检查看房记录是否已有待处理的合约申请"""
    application = db.query(ContractApplication).filter(
        ContractApplication.booking_id == booking_id,
        ContractApplication.status == ContractApplicationStatus.APPLY_PENDING
    ).first()
    return application is not None
