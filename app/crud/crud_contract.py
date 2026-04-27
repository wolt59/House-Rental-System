from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.schemas.contract import ContractCreate, ContractUpdate


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
        status="pending_sign",
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


def update_contract(db: Session, db_contract: Contract, contract_in: ContractUpdate) -> Contract:
    for field, value in contract_in.dict(exclude_unset=True).items():
        setattr(db_contract, field, value)
    db.commit()
    db.refresh(db_contract)
    return db_contract
