from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_active_admin, get_db
from app.crud import crud_audit, crud_payment, crud_contract
from app.schemas.payment import Payment as PaymentSchema, PaymentCreate, PaymentUpdate

router = APIRouter()


@router.post("/", response_model=PaymentSchema, status_code=status.HTTP_201_CREATED)
def create_payment(payment_in: PaymentCreate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    contract = crud_contract.get_contract(db, payment_in.contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if contract.tenant_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    payment = crud_payment.create_payment(db, tenant_id=contract.tenant_id, payment_in=payment_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="create_payment",
        target_type="payment",
        target_id=payment.id,
        detail=f"Payment created for contract {payment.contract_id}, amount={payment.amount}",
        ip_address=ip_address,
    )
    return payment


@router.get("/", response_model=List[PaymentSchema])
def list_payments(
    contract_id: int = None,
    status: str = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    if current_user.role == "admin":
        return crud_payment.get_payments(db, contract_id=contract_id, status=status, skip=skip, limit=limit)
    elif current_user.role == "landlord":
        from app.models.payment import Payment
        from app.models.contract import Contract
        query = db.query(Payment).join(Contract).filter(Contract.landlord_id == current_user.id)
        if contract_id is not None:
            query = query.filter(Payment.contract_id == contract_id)
        if status is not None:
            query = query.filter(Payment.status == status)
        return query.offset(skip).limit(limit).all()
    else:
        return crud_payment.get_payments(db, tenant_id=current_user.id, contract_id=contract_id, status=status, skip=skip, limit=limit)


@router.get("/{payment_id}", response_model=PaymentSchema)
def read_payment(payment_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    payment = crud_payment.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    contract = crud_contract.get_contract(db, payment.contract_id)
    if current_user.role != "admin" and payment.tenant_id != current_user.id and (not contract or contract.landlord_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return payment


@router.put("/{payment_id}", response_model=PaymentSchema)
def update_payment(payment_id: int, payment_in: PaymentUpdate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    payment = crud_payment.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    contract = crud_contract.get_contract(db, payment.contract_id)
    if current_user.role != "admin" and payment.tenant_id != current_user.id and (not contract or contract.landlord_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    updated = crud_payment.update_payment(db, payment, payment_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_payment",
        target_type="payment",
        target_id=updated.id,
        detail=f"Payment updated, status={updated.status}",
        ip_address=ip_address,
    )
    return updated
