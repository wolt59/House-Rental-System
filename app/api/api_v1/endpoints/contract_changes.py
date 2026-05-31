from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.contract_change_request import (
    ContractChangeRequestCreate,
    ContractChangeRequestResponse,
    ContractChangeRequest as ContractChangeRequestSchema,
)
from app.crud import crud_contract_change
from app.core.enums import UserRole

router = APIRouter()


@router.post("/", response_model=ContractChangeRequestSchema, status_code=status.HTTP_201_CREATED)
def create_change_request(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request_in: ContractChangeRequestCreate,
):
    """发起合同变更申请"""
    try:
        change_request = crud_contract_change.create_contract_change_request(
            db=db,
            initiator_id=current_user.id,
            request_in=request_in
        )
        return change_request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[ContractChangeRequestSchema])
def list_change_requests(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
    contract_id: Optional[int] = None,
    status: Optional[str] = None,
):
    """获取合同变更申请列表"""
    if current_user.role == UserRole.TENANT:
        # 租客查看自己发起或收到的申请
        requests = crud_contract_change.get_contract_change_requests(
            db=db,
            tenant_id=current_user.id,
            contract_id=contract_id,
            status=status,
            skip=skip,
            limit=limit
        )
    elif current_user.role == UserRole.LANDLORD:
        # 房东查看自己发起或收到的申请
        requests = crud_contract_change.get_contract_change_requests(
            db=db,
            landlord_id=current_user.id,
            contract_id=contract_id,
            status=status,
            skip=skip,
            limit=limit
        )
    else:
        # 管理员查看所有
        requests = crud_contract_change.get_contract_change_requests(
            db=db,
            contract_id=contract_id,
            status=status,
            skip=skip,
            limit=limit
        )
    
    return requests


@router.get("/{request_id}", response_model=ContractChangeRequestSchema)
def get_change_request(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request_id: int,
):
    """获取单个合同变更申请详情"""
    change_request = crud_contract_change.get_contract_change_request(
        db=db,
        request_id=request_id
    )
    
    if not change_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同变更申请不存在"
        )
    
    # 权限检查
    contract = change_request.contract
    if current_user.id not in [contract.tenant_id, contract.landlord_id]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看此申请")
    
    return change_request


@router.post("/{request_id}/approve", response_model=ContractChangeRequestSchema)
def approve_change_request(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request_id: int,
    response_data: ContractChangeRequestResponse,
):
    """同意合同变更申请"""
    change_request = crud_contract_change.get_contract_change_request(
        db=db,
        request_id=request_id
    )
    
    if not change_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同变更申请不存在"
        )
    
    # 验证权限：只有合同另一方可以同意
    contract = change_request.contract
    if current_user.id == change_request.initiator_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="发起人不能审批自己的申请")
    if current_user.id not in [contract.tenant_id, contract.landlord_id]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权处理此申请")
    
    try:
        change_request = crud_contract_change.approve_contract_change_request(
            db=db,
            request=change_request,
            responder_id=current_user.id,
            response_opinion=response_data.opinion
        )
        return change_request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{request_id}/reject", response_model=ContractChangeRequestSchema)
def reject_change_request(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request_id: int,
    reason: str,
):
    """拒绝合同变更申请"""
    change_request = crud_contract_change.get_contract_change_request(
        db=db,
        request_id=request_id
    )
    
    if not change_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合同变更申请不存在"
        )
    
    # 验证权限
    contract = change_request.contract
    if current_user.id == change_request.initiator_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="发起人不能审批自己的申请")
    if current_user.id not in [contract.tenant_id, contract.landlord_id]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权处理此申请")
    
    try:
        change_request = crud_contract_change.reject_contract_change_request(
            db=db,
            request=change_request,
            responder_id=current_user.id,
            reason=reason
        )
        return change_request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
