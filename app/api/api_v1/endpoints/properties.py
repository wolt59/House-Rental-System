from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_active_admin,
    get_current_active_landlord,
    get_current_active_user,
    get_current_user_optional,
    get_db,
)
from app.crud import crud_audit, crud_property
from app.models.message import Message as MessageModel
from app.models.property import Property as PropertyModel
from app.schemas.property import (
    Property,
    PropertyCreate,
    PropertyReview,
    PropertyStatusUpdate,
    PropertyUpdate,
)
from app.core.enums import PropertyReviewStatus, PropertyStatus

router = APIRouter()

# 核心字段（修改需重新审核）
CORE_PROPERTY_FIELDS = {"address", "floor_plan", "area", "rent", "deposit", "floor_number", "total_floors"}


@router.get("/", response_model=List[Property])
def list_properties(
    skip: int = 0,
    limit: int = 20,
    region: Optional[str] = None,
    floor_plan: Optional[str] = None,
    status: Optional[str] = None,
    review_status: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """
    获取房源列表
    - 管理员：可查看所有状态的房源
    - 房东：可查看自己的所有房源
    - 普通用户（租客）：只能查看已审核通过且已发布的房源
    """
    # 管理员可以看到所有状态的房源
    if current_user and current_user.role == "admin":
        filter_review_status = review_status
        filter_status = status
    # 房东查看自己的房源时，可以看到所有状态
    elif current_user and current_user.role == "landlord":
        # 如果是房东查看自己的房源，在 my 接口中处理
        filter_review_status = review_status
        filter_status = status
    else:
        # 普通用户（租客）只能看到已审核通过且已发布的房源
        filter_review_status = PropertyReviewStatus.APPROVED
        # 只显示 published 或 vacant 状态的房源（不显示 unpublished）
        if status:
            filter_status = status
        else:
            filter_status = PropertyStatus.PUBLISHED  # 默认只显示已发布
    
    return crud_property.get_properties(
        db,
        skip=skip,
        limit=limit,
        region=region,
        floor_plan=floor_plan,
        review_status=filter_review_status,
        status=filter_status,
        keyword=keyword,
    )


@router.get("/my", response_model=List[Property])
def list_my_properties(
    skip: int = 0,
    limit: int = 20,
    region: Optional[str] = None,
    floor_plan: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_landlord),
):
    return crud_property.get_properties(
        db,
        skip=skip,
        limit=limit,
        region=region,
        floor_plan=floor_plan,
        owner_id=current_user.id,
    )


@router.get("/owner/{owner_id}", response_model=List[Property])
def list_owner_properties(
    owner_id: int,
    skip: int = 0,
    limit: int = 20,
    review_status: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_admin),
):
    return crud_property.get_properties(
        db,
        skip=skip,
        limit=limit,
        owner_id=owner_id,
        review_status=review_status,
        status=status,
    )


@router.post("/", response_model=Property, status_code=status.HTTP_201_CREATED)
def create_property(property_in: PropertyCreate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_landlord)):
    """创建房源（草稿状态）"""
    property_obj = crud_property.create_property(db, owner_id=current_user.id, property_in=property_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="create_property",
        target_type="property",
        target_id=property_obj.id,
        detail=f"Property created as draft",
        ip_address=ip_address,
    )
    return property_obj


@router.get("/{property_id}", response_model=Property)
def read_property(property_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
    db_property = crud_property.get_property(db, property_id=property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if (
        db_property.review_status != PropertyReviewStatus.APPROVED
        and (not current_user or db_property.owner_id != current_user.id)
        and (not current_user or current_user.role != "admin")
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return db_property


@router.put("/{property_id}", response_model=Property)
def update_property(
    property_id: int,
    property_in: PropertyUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_landlord),
):
    """
    更新房源信息
    - 草稿状态：可修改所有字段
    - 待审核/审核中：只能修改描述和图片
    - 已通过/已发布：非核心字段可直接修改，核心字段需重新审核
    - 已出租/维修中：只能修改描述和备注
    """
    db_property = crud_property.get_property(db, property_id=property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if db_property.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    # 获取要更新的字段
    update_data = property_in.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    
    # 检查权限和限制
    review_status = db_property.review_status
    property_status = db_property.status
    modified_fields = set(update_data.keys())
    
    # 标记是否需要系统自动修改审核状态（修改核心字段时）
    needs_review_status_change = False
    
    # 根据状态限制可修改的字段
    if review_status == PropertyReviewStatus.DRAFT:
        # 草稿状态：可以修改所有字段
        pass
    elif review_status in [PropertyReviewStatus.PENDING, PropertyReviewStatus.REVIEWING]:
        # 待审核/审核中：只能修改描述、图片、视频等非核心信息
        allowed_fields = {"description", "video_url", "facilities", "surrounding"}
        disallowed = modified_fields - allowed_fields
        if disallowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot modify these fields during review: {', '.join(disallowed)}"
            )
    elif review_status == PropertyReviewStatus.APPROVED:
        # 已通过状态
        if property_status in [PropertyStatus.RENTED, PropertyStatus.MAINTENANCE]:
            # 已出租或维修中：只能修改描述
            allowed_fields = {"description"}
            disallowed = modified_fields - allowed_fields
            if disallowed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot modify fields when property is {property_status}. Only description can be updated."
                )
        else:
            # published/unpublished/vacant：检查是否修改了核心字段
            core_fields_modified = modified_fields & CORE_PROPERTY_FIELDS
            if core_fields_modified:
                # 修改了核心字段，标记需要修改审核状态
                needs_review_status_change = True
    elif review_status == PropertyReviewStatus.REJECTED:
        # 被拒绝：可以自由修改，准备重新提交
        pass
    
    # 在权限检查之前，将系统自动的 review_status 修改加入 update_data
    if needs_review_status_change:
        update_data["review_status"] = PropertyReviewStatus.PENDING.value
        update_data["submitted_at"] = datetime.utcnow()
    
    # 房东不能手动修改审核状态（系统自动修改的除外）
    if "review_status" in modified_fields and current_user.role != "admin" and not needs_review_status_change:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can update review status")
    
    # 使用 update_data 而不是 property_in，因为 update_data 包含了系统自动添加的字段
    for field, value in update_data.items():
        setattr(db_property, field, value)
    db.commit()
    db.refresh(db_property)
    
    updated = db_property
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_property",
        target_type="property",
        target_id=updated.id,
        detail=f"Updated property fields: {list(modified_fields)}",
        ip_address=ip_address,
    )
    return updated


@router.put("/{property_id}/review", response_model=Property)
def review_property(
    property_id: int,
    review_in: PropertyReview,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_admin),
):
    """管理员审核房源（支持开始审核、通过、拒绝）"""
    db_property = crud_property.get_property(db, property_id=property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    
    ip_address = request.client.host if request.client else None
    
    # 如果当前状态是 pending，先转为 reviewing
    if db_property.review_status == PropertyReviewStatus.PENDING:
        try:
            db_property = crud_property.start_review(db, db_property)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    # 执行审核操作
    if review_in.review_status == PropertyReviewStatus.APPROVED:
        try:
            updated = crud_property.approve_property(db, db_property, review_in.comment)
            action_detail = f"Property approved. Comment: {review_in.comment or 'none'}"
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    elif review_in.review_status == PropertyReviewStatus.REJECTED:
        if not review_in.comment:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reject comment is required")
        try:
            updated = crud_property.reject_property(db, db_property, review_in.comment)
            action_detail = f"Property rejected. Comment: {review_in.comment}"
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid review status")
    
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="review_property",
        target_type="property",
        target_id=updated.id,
        detail=action_detail,
        ip_address=ip_address,
    )
    
    # 发送通知
    notification_content = (
        f"Your property '{updated.title}' review status is now '{updated.review_status}'. "
        f"Comment: {review_in.comment or 'none'}."
    )
    notification = MessageModel(
        from_user_id=current_user.id,
        to_user_id=updated.owner_id,
        property_id=updated.id,
        content=notification_content,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    return updated


@router.put("/{property_id}/status", response_model=Property)
def change_property_status(
    property_id: int,
    status_in: PropertyStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    db_property = crud_property.get_property(db, property_id=property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if current_user.role == "tenant":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenants cannot change property status")
    if current_user.role == "landlord" and db_property.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if db_property.review_status != PropertyReviewStatus.APPROVED and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change property status before approval")
    if status_in.status not in {PropertyStatus.VACANT, PropertyStatus.RENTED, PropertyStatus.MAINTENANCE}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid property status")
    db_property.status = status_in.status
    db.commit()
    db.refresh(db_property)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_property_status",
        target_type="property",
        target_id=db_property.id,
        detail=f"Property status changed to {status_in.status}",
        ip_address=ip_address,
    )
    return db_property


@router.delete("/{property_id}", response_model=Property)
def delete_property(property_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_landlord)):
    db_property = crud_property.get_property(db, property_id=property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if db_property.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    removed = crud_property.remove_property(db, db_property)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="delete_property",
        target_type="property",
        target_id=removed.id,
        detail="Property deleted",
        ip_address=ip_address,
    )
    return removed


@router.post("/{property_id}/submit-review", response_model=Property)
def submit_for_review(property_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_landlord)):
    """房东提交房源审核"""
    db_property = crud_property.get_property(db, property_id=property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if db_property.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    try:
        updated = crud_property.submit_for_review(db, db_property)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="submit_property_review",
        target_type="property",
        target_id=updated.id,
        detail="Property submitted for review",
        ip_address=ip_address,
    )
    return updated


@router.post("/{property_id}/unpublish", response_model=Property)
def unpublish_property(
    property_id: int,
    request: Request,
    data: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """暂停发布房源（房东或管理员均可操作）"""
    db_property = crud_property.get_property(db, property_id=property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    
    # 权限检查：房东只能操作自己的房源，管理员可以操作所有
    if current_user.role == "admin":
        reason = data.get("reason", "") if data else ""
        # 管理员下架：同时变为待审核和未发布
        try:
            updated = crud_property.admin_unpublish_property(db, db_property, reason=reason)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    elif db_property.owner_id == current_user.id:
        reason = "房东主动取消发布"
        # 房东取消发布：只修改状态为未发布，不影响审核状态
        try:
            updated = crud_property.unpublish_property(db, db_property)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="unpublish_property",
        target_type="property",
        target_id=updated.id,
        detail=f"Property unpublished: {reason}",
        ip_address=ip_address,
    )
    return updated


@router.post("/{property_id}/republish", response_model=Property)
def republish_property(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """重新发布房源（房东或管理员均可操作）"""
    db_property = crud_property.get_property(db, property_id=property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    
    # 权限检查：房东只能操作自己的房源，管理员可以操作所有
    if current_user.role != "admin" and db_property.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    try:
        updated = crud_property.republish_property(db, db_property)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="republish_property",
        target_type="property",
        target_id=updated.id,
        detail="Property republished",
        ip_address=ip_address,
    )
    return updated


@router.put("/{property_id}/admin-unpublish", response_model=Property)
def admin_unpublish_property(
    property_id: int,
    reason: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_admin),
):
    """管理员强制下架房源"""
    db_property = crud_property.get_property(db, property_id=property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    
    try:
        updated = crud_property.admin_unpublish_property(db, db_property, reason)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="admin_unpublish_property",
        target_type="property",
        target_id=updated.id,
        detail=f"Property unpublished by admin. Reason: {reason or 'Not specified'}",
        ip_address=ip_address,
    )
    return updated
