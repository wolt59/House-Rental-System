from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.contract_application import (
    ContractApplicationCreate,
    ContractApplicationResponse,
    ContractApplication as ContractApplicationSchema
)
from app.crud import crud_contract_application
from app.core.enums import UserRole

router = APIRouter()


@router.post("/", response_model=ContractApplicationSchema, status_code=status.HTTP_201_CREATED)
def create_application(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    application_in: ContractApplicationCreate,
):
    """租客发起合约申请（只有看房完成后才能发起）"""
    if current_user.role != UserRole.TENANT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有租客可以发起合约申请"
        )
    
    try:
        application = crud_contract_application.create_contract_application(
            db=db,
            tenant_id=current_user.id,
            application_in=application_in
        )
        return application
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[ContractApplicationSchema])
def list_applications(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
    property_id: Optional[int] = None,
    status: Optional[str] = None,
):
    """获取合约申请列表（根据角色自动过滤）"""
    if current_user.role == UserRole.TENANT:
        applications = crud_contract_application.get_contract_applications(
            db=db,
            tenant_id=current_user.id,
            property_id=property_id,
            status=status,
            skip=skip,
            limit=limit
        )
    elif current_user.role == UserRole.LANDLORD:
        applications = crud_contract_application.get_contract_applications(
            db=db,
            landlord_id=current_user.id,
            property_id=property_id,
            status=status,
            skip=skip,
            limit=limit
        )
    else:
        # 管理员可以查看所有申请
        applications = crud_contract_application.get_contract_applications(
            db=db,
            property_id=property_id,
            status=status,
            skip=skip,
            limit=limit
        )
    
    return applications


@router.get("/{application_id}", response_model=ContractApplicationSchema)
def get_application(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    application_id: int,
):
    """获取单个合约申请详情"""
    application = crud_contract_application.get_contract_application(
        db=db,
        application_id=application_id
    )
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合约申请不存在"
        )
    
    # 权限检查：只有相关用户可以查看
    if current_user.role == UserRole.TENANT and application.tenant_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看此申请")
    if current_user.role == UserRole.LANDLORD and application.landlord_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看此申请")
    
    return application


@router.post("/{application_id}/approve", response_model=ContractApplicationSchema)
def approve_application(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    application_id: int,
    response_data: ContractApplicationResponse,
):
    """房东同意合约申请，生成合同草稿"""
    if current_user.role != UserRole.LANDLORD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有房东可以处理合约申请"
        )
    
    application = crud_contract_application.get_contract_application(
        db=db,
        application_id=application_id
    )
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合约申请不存在"
        )
    
    try:
        application = crud_contract_application.approve_contract_application(
            db=db,
            application=application,
            landlord_id=current_user.id,
            response=response_data.response
        )
        return application
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{application_id}/reject", response_model=ContractApplicationSchema)
def reject_application(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    application_id: int,
    reason: str,
):
    """房东拒绝合约申请"""
    if current_user.role != UserRole.LANDLORD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有房东可以处理合约申请"
        )
    
    application = crud_contract_application.get_contract_application(
        db=db,
        application_id=application_id
    )
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合约申请不存在"
        )
    
    try:
        application = crud_contract_application.reject_contract_application(
            db=db,
            application=application,
            landlord_id=current_user.id,
            reason=reason
        )
        return application
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{application_id}/cancel", response_model=ContractApplicationSchema)
def cancel_application(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    application_id: int,
):
    """租客取消合约申请"""
    if current_user.role != UserRole.TENANT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有租客可以取消合约申请"
        )
    
    application = crud_contract_application.get_contract_application(
        db=db,
        application_id=application_id
    )
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="合约申请不存在"
        )
    
    try:
        application = crud_contract_application.cancel_contract_application(
            db=db,
            application=application,
            tenant_id=current_user.id
        )
        return application
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
