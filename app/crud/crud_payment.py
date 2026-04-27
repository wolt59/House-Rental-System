from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.schemas.payment import PaymentCreate, PaymentUpdate


def _generate_payment_no() -> str:
    return f"PAY{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"


def get_payment(db: Session, payment_id: int) -> Optional[Payment]:
    return db.query(Payment).filter(Payment.id == payment_id).first()


def get_payments(
    db: Session,
    contract_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[Payment]:
    query = db.query(Payment)
    if contract_id is not None:
        query = query.filter(Payment.contract_id == contract_id)
    if tenant_id is not None:
        query = query.filter(Payment.tenant_id == tenant_id)
    if status is not None:
        query = query.filter(Payment.status == status)
    return query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()


def create_payment(db: Session, tenant_id: int, payment_in: PaymentCreate) -> Payment:
    payment = Payment(
        payment_no=_generate_payment_no(),
        contract_id=payment_in.contract_id,
        tenant_id=tenant_id,
        amount=payment_in.amount,
        payment_method=payment_in.payment_method,
        due_date=payment_in.due_date,
        remark=payment_in.remark,
        status="pending",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def update_payment(db: Session, db_payment: Payment, payment_in: PaymentUpdate) -> Payment:
    update_data = payment_in.dict(exclude_unset=True)
    if payment_in.status == "paid" and db_payment.status != "paid":
        update_data["paid_at"] = datetime.utcnow()
    for field, value in update_data.items():
        setattr(db_payment, field, value)
    db.commit()
    db.refresh(db_payment)
    return db_payment
