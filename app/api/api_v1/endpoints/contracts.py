from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_active_admin, get_current_active_landlord, get_db
from app.crud import crud_audit, crud_contract
from app.models.contract import Contract
from app.models.property import Property
from app.schemas.contract import Contract as ContractSchema, ContractCreate, ContractUpdate

router = APIRouter()


@router.post("/", response_model=ContractSchema, status_code=status.HTTP_201_CREATED)
def create_contract(contract_in: ContractCreate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_landlord)):
    property_obj = db.query(Property).filter(Property.id == contract_in.property_id).first()
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if property_obj.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create contract for this property")
    if property_obj.review_status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Property must be approved before creating contract")
    contract = crud_contract.create_contract(db, landlord_id=current_user.id, contract_in=contract_in)
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


@router.get("/", response_model=List[ContractSchema])
def list_contracts(
    skip: int = 0,
    limit: int = 20,
    status: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    if current_user.role == "admin":
        return crud_contract.get_contracts(db, status=status, skip=skip, limit=limit)
    elif current_user.role == "landlord":
        return crud_contract.get_contracts(db, landlord_id=current_user.id, status=status, skip=skip, limit=limit)
    else:
        return crud_contract.get_contracts(db, tenant_id=current_user.id, status=status, skip=skip, limit=limit)


@router.get("/{contract_id}", response_model=ContractSchema)
def read_contract(contract_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    contract = crud_contract.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if current_user.role != "admin" and contract.landlord_id != current_user.id and contract.tenant_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return contract


@router.put("/{contract_id}", response_model=ContractSchema)
def update_contract(contract_id: int, contract_in: ContractUpdate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    contract = crud_contract.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if contract.landlord_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if contract.status not in ("pending_sign", "draft"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot update a signed/active contract")
    updated = crud_contract.update_contract(db, contract, contract_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_contract",
        target_type="contract",
        target_id=updated.id,
        detail=f"Contract updated",
        ip_address=ip_address,
    )
    return updated


@router.put("/{contract_id}/sign/landlord", response_model=ContractSchema)
def sign_contract_landlord(contract_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_landlord)):
    contract = crud_contract.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if contract.landlord_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if contract.signed_by_landlord:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already signed by landlord")
    contract.signed_by_landlord = 1
    if contract.signed_by_tenant:
        contract.status = "active"
    else:
        contract.status = "pending_tenant_sign"
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
def sign_contract_tenant(contract_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    contract = crud_contract.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if contract.tenant_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if contract.signed_by_tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already signed by tenant")
    contract.signed_by_tenant = 1
    if contract.signed_by_landlord:
        contract.status = "active"
    else:
        contract.status = "pending_landlord_sign"
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


@router.put("/{contract_id}/terminate", response_model=ContractSchema)
def terminate_contract(contract_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    contract = crud_contract.get_contract(db, contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    if contract.landlord_id != current_user.id and contract.tenant_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if contract.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only active contracts can be terminated")
    contract.status = "terminated"
    db.commit()
    db.refresh(contract)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="terminate_contract",
        target_type="contract",
        target_id=contract.id,
        detail="Contract terminated",
        ip_address=ip_address,
    )
    return contract
