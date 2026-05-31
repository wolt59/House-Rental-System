from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.contract_termination_request import (
    ContractTerminationRequestCreate,
    ContractTerminationRequest as ContractTerminationRequestSchema,
)
from app.crud import crud_contract_change
from app.core.enums import UserRole

router = APIRouter()


@router.post("/", response_model=ContractTerminationRequestSchema, status_code=status.HTTP_201_CREATED)
def create_termination_request(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request_in: ContractTerminationRequestCreate,
):
    """发起提前解约申请"""
    try:
        termination_request = crud_contract_change.create_contract_termination_request(
            db=db,
            initiator_id=current_user.id,
            request_in=request_in
        )
        return termination_request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[ContractTerminationRequestSchema])
def list_termination_requests(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
    contract_id: Optional[int] = None,
    status: Optional[str] = None,
):
    """获取提前解约申请列表"""
    if current_user.role == UserRole.TENANT:
        requests = crud_contract_change.get_contract_termination_requests_by_role(
            db=db,
            tenant_id=current_user.id,
            contract_id=contract_id,
            status=status,
            skip=skip,
            limit=limit
        )
    elif current_user.role == UserRole.LANDLORD:
        requests = crud_contract_change.get_contract_termination_requests_by_role(
            db=db,
            landlord_id=current_user.id,
            contract_id=contract_id,
            status=status,
            skip=skip,
            limit=limit
        )
    else:
        # Admin 或其他角色
        requests = crud_contract_change.get_contract_termination_requests(
            db=db,
            contract_id=contract_id,
            status=status,
            skip=skip,
            limit=limit
        )
    
    return requests


@router.get("/{request_id}", response_model=ContractTerminationRequestSchema)
def get_termination_request(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request_id: int,
):
    """获取单个提前解约申请详情"""
    termination_request = crud_contract_change.get_contract_termination_request(
        db=db,
        request_id=request_id
    )
    
    if not termination_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提前解约申请不存在"
        )
    
    # 权限检查
    contract = termination_request.contract
    if current_user.id not in [contract.tenant_id, contract.landlord_id]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看此申请")
    
    return termination_request


@router.post("/{request_id}/approve", response_model=ContractTerminationRequestSchema)
def approve_termination_request(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request_id: int,
    opinion: Optional[str] = None,
):
    """同意提前解约申请"""
    termination_request = crud_contract_change.get_contract_termination_request(
        db=db,
        request_id=request_id
    )
    
    if not termination_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提前解约申请不存在"
        )
    
    # 验证权限
    contract = termination_request.contract
    if current_user.id == termination_request.initiator_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="发起人不能审批自己的申请")
    if current_user.id not in [contract.tenant_id, contract.landlord_id]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权处理此申请")
    
    try:
        termination_request = crud_contract_change.approve_contract_termination_request(
            db=db,
            request=termination_request,
            responder_id=current_user.id,
            response_opinion=opinion
        )
        return termination_request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{request_id}/reject", response_model=ContractTerminationRequestSchema)
def reject_termination_request(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request_id: int,
    reason: str,
):
    """拒绝提前解约申请"""
    termination_request = crud_contract_change.get_contract_termination_request(
        db=db,
        request_id=request_id
    )
    
    if not termination_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提前解约申请不存在"
        )
    
    # 验证权限
    contract = termination_request.contract
    if current_user.id == termination_request.initiator_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="发起人不能审批自己的申请")
    if current_user.id not in [contract.tenant_id, contract.landlord_id]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权处理此申请")
    
    try:
        termination_request = crud_contract_change.reject_contract_termination_request(
            db=db,
            request=termination_request,
            responder_id=current_user.id,
            response_opinion=reason
        )
        return termination_request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
