from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.payment import Payment
from app.models.contract import Contract
from app.models.property import Property
from app.schemas.payment import PaymentCreate, PaymentSubmit, PaymentUpdate
from app.core.enums import PaymentStatus, BillType, ContractStatus


import uuid


def _generate_bill_no() -> str:
    return f"BILL{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"


def _generate_payment_no() -> str:
    return f"PAY{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"


def get_payment(db: Session, payment_id: int) -> Optional[Payment]:
    return db.query(Payment).filter(Payment.id == payment_id).first()


def get_payment_by_bill_no(db: Session, bill_no: str) -> Optional[Payment]:
    return db.query(Payment).filter(Payment.bill_no == bill_no).first()


def get_payments(
    db: Session,
    contract_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    landlord_id: Optional[int] = None,
    property_id: Optional[int] = None,
    property_title: Optional[str] = None,
    status: Optional[str] = None,
    bill_type: Optional[str] = None,
    due_date_from: Optional[datetime] = None,
    due_date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[Payment]:
    query = db.query(Payment)
    if contract_id is not None:
        query = query.filter(Payment.contract_id == contract_id)
    if tenant_id is not None:
        query = query.filter(Payment.tenant_id == tenant_id)
    if landlord_id is not None:
        query = query.filter(Payment.landlord_id == landlord_id)
    if property_id is not None:
        query = query.filter(Payment.property_id == property_id)
    if property_title:
        query = query.join(Property, Payment.property_id == Property.id).filter(
            Property.title.ilike(f"%{property_title}%")
        )
    if status is not None:
        query = query.filter(Payment.status == status)
    if bill_type is not None:
        query = query.filter(Payment.bill_type == bill_type)
    if due_date_from is not None:
        query = query.filter(Payment.due_date >= due_date_from)
    if due_date_to is not None:
        query = query.filter(Payment.due_date <= due_date_to)
    return query.order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()


def get_payments_count(
    db: Session,
    contract_id: Optional[int] = None,
    tenant_id: Optional[int] = None,
    landlord_id: Optional[int] = None,
    property_id: Optional[int] = None,
    status: Optional[str] = None,
    bill_type: Optional[str] = None,
    due_date_from: Optional[datetime] = None,
    due_date_to: Optional[datetime] = None,
) -> int:
    query = db.query(Payment)
    if contract_id is not None:
        query = query.filter(Payment.contract_id == contract_id)
    if tenant_id is not None:
        query = query.filter(Payment.tenant_id == tenant_id)
    if landlord_id is not None:
        query = query.filter(Payment.landlord_id == landlord_id)
    if property_id is not None:
        query = query.filter(Payment.property_id == property_id)
    if status is not None:
        query = query.filter(Payment.status == status)
    if bill_type is not None:
        query = query.filter(Payment.bill_type == bill_type)
    if due_date_from is not None:
        query = query.filter(Payment.due_date >= due_date_from)
    if due_date_to is not None:
        query = query.filter(Payment.due_date <= due_date_to)
    return query.count()


def create_payment(db: Session, tenant_id: int, payment_in: PaymentCreate) -> Payment:
    """创建单笔账单"""
    payment = Payment(
        bill_no=_generate_bill_no(),
        contract_id=payment_in.contract_id,
        property_id=payment_in.property_id,
        landlord_id=payment_in.landlord_id,
        tenant_id=tenant_id,
        bill_type=payment_in.bill_type,
        period=payment_in.period,
        due_amount=payment_in.due_amount,
        due_date=payment_in.due_date,
        remark=payment_in.remark,
        status=PaymentStatus.PENDING,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def update_payment(db: Session, db_payment: Payment, payment_in: PaymentUpdate) -> Payment:
    """管理员更新账单"""
    update_data = payment_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_payment, field, value)
    db.commit()
    db.refresh(db_payment)
    return db_payment


def submit_payment(db: Session, db_payment: Payment, submit_in: PaymentSubmit) -> Payment:
    """租客提交付款凭证"""
    db_payment.status = PaymentStatus.SUBMITTED
    db_payment.actual_amount = submit_in.actual_amount
    db_payment.payment_method = submit_in.payment_method
    db_payment.payment_time = submit_in.payment_time or datetime.utcnow()
    db_payment.transaction_note = submit_in.transaction_note
    db_payment.payment_proof = submit_in.payment_proof
    db_payment.payment_no = _generate_payment_no()
    db_payment.paid_at = datetime.utcnow()
    db.commit()
    db.refresh(db_payment)
    return db_payment


def confirm_payment(db: Session, db_payment: Payment) -> Payment:
    """房东确认收款"""
    db_payment.status = PaymentStatus.CONFIRMED
    db_payment.confirmed_at = datetime.utcnow()
    db.commit()
    db.refresh(db_payment)
    return db_payment


def reject_payment(db: Session, db_payment: Payment, rejected_reason: str) -> Payment:
    """房东驳回付款"""
    db_payment.status = PaymentStatus.REJECTED
    db_payment.rejected_reason = rejected_reason
    db.commit()
    db.refresh(db_payment)
    return db_payment


def cancel_payment(db: Session, db_payment: Payment) -> Payment:
    """取消账单"""
    db_payment.status = PaymentStatus.CANCELLED
    db.commit()
    db.refresh(db_payment)
    return db_payment


def generate_bills_for_contract(db: Session, contract: Contract) -> List[Payment]:
    """根据合同自动生成押金和租金账单"""
    bills = []
    now = datetime.utcnow()

    # 1. 生成押金账单
    if contract.deposit and contract.deposit > 0:
        deposit_bill = Payment(
            bill_no=_generate_bill_no(),
            contract_id=contract.id,
            property_id=contract.property_id,
            landlord_id=contract.landlord_id,
            tenant_id=contract.tenant_id,
            bill_type=BillType.DEPOSIT,
            period=None,
            due_amount=contract.deposit,
            due_date=contract.start_date,
            status=PaymentStatus.PENDING,
        )
        db.add(deposit_bill)
        bills.append(deposit_bill)

    # 2. 生成租金账单
    start_date = contract.start_date
    end_date = contract.end_date
    payment_day = contract.payment_day or 1

    current = start_date
    while current < end_date:
        year = current.year
        month = current.month
        period = f"{year}-{month:02d}"

        # 计算付款截止日
        if payment_day > 28:
            due_day = min(payment_day, 28)
        else:
            due_day = payment_day
        due_date = datetime(year, month, due_day) if current == start_date else current.replace(day=due_day)

        rent_bill = Payment(
            bill_no=_generate_bill_no(),
            contract_id=contract.id,
            property_id=contract.property_id,
            landlord_id=contract.landlord_id,
            tenant_id=contract.tenant_id,
            bill_type=BillType.RENT,
            period=period,
            due_amount=contract.monthly_rent,
            due_date=due_date,
            status=PaymentStatus.PENDING,
        )
        db.add(rent_bill)
        bills.append(rent_bill)

        # 下一个月
        if month == 12:
            current = current.replace(year=year + 1, month=1)
        else:
            current = current.replace(month=month + 1)

    db.commit()
    for bill in bills:
        db.refresh(bill)
    return bills


def generate_next_month_bills(db: Session) -> List[Payment]:
    """定时任务：为活跃合同生成下月账单（每月25日调用）"""
    now = datetime.utcnow()
    next_month = now.replace(day=1) + timedelta(days=32)
    next_month = next_month.replace(day=1)
    period = f"{next_month.year}-{next_month.month:02d}"

    contracts = db.query(Contract).filter(
        Contract.status == ContractStatus.ACTIVE,
        Contract.end_date > next_month
    ).all()

    bills = []
    for contract in contracts:
        existing = db.query(Payment).filter(
            and_(
                Payment.contract_id == contract.id,
                Payment.period == period,
                Payment.bill_type == BillType.RENT,
            )
        ).first()
        if existing:
            continue

        payment_day = contract.payment_day or 1
        if payment_day > 28:
            due_day = min(payment_day, 28)
        else:
            due_day = payment_day
        due_date = next_month.replace(day=due_day)

        bill = Payment(
            bill_no=_generate_bill_no(),
            contract_id=contract.id,
            property_id=contract.property_id,
            landlord_id=contract.landlord_id,
            tenant_id=contract.tenant_id,
            bill_type=BillType.RENT,
            period=period,
            due_amount=contract.monthly_rent,
            due_date=due_date,
            status=PaymentStatus.PENDING,
        )
        db.add(bill)
        bills.append(bill)

    if bills:
        db.commit()
        for bill in bills:
            db.refresh(bill)
    return bills


def check_and_mark_overdue(db: Session) -> int:
    """定时任务：检查并标记逾期账单"""
    now = datetime.utcnow()
    overdue_bills = db.query(Payment).filter(
        and_(
            Payment.status == PaymentStatus.PENDING,
            Payment.due_date < now,
        )
    ).all()

    count = 0
    for bill in overdue_bills:
        bill.status = PaymentStatus.OVERDUE
        bill.overdue_days = (now - bill.due_date).days
        count += 1

    if count > 0:
        db.commit()
    return count


def cancel_bills_for_contract(db: Session, contract_id: int, after_date: datetime = None) -> int:
    """合同终止/取消时，取消未完成账单"""
    query = db.query(Payment).filter(
        and_(
            Payment.contract_id == contract_id,
            Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.SUBMITTED, PaymentStatus.OVERDUE]),
        )
    )
    if after_date:
        query = query.filter(Payment.due_date >= after_date)

    bills = query.all()
    for bill in bills:
        bill.status = PaymentStatus.CANCELLED

    if bills:
        db.commit()
    return len(bills)
