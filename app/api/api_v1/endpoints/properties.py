from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_active_admin,
    get_current_active_landlord,
    get_current_active_user,
    get_current_user_optional,
    get_db,
)
from app.cache import cache_manager, CacheKey, invalidate_property_cache
from app.core.config import settings
from app.crud import crud_audit, crud_property, crud_message
from app.models.message import Message as MessageModel
from app.models.property import Property as PropertyModel
from app.models.user import User
from app.api.websocket import ws_manager
from app.schemas.property import (
    Property,
    PropertyCreate,
    PropertyReview,
    PropertyStatusUpdate,
    PropertyUpdate,
)
from app.schemas.common import PaginatedResponse
from app.core.enums import PropertyReviewStatus, PropertyStatus

router = APIRouter()

# 核心字段（修改需重新审核）
CORE_PROPERTY_FIELDS = {"address", "floor_plan", "area", "rent", "deposit", "floor_number", "total_floors"}


@router.get("/")
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

    # 构建缓存键
    user_role = current_user.role if current_user else "anonymous"
    cache_key = CacheKey.property_list(
        skip=skip, limit=limit, region=region, floor_plan=floor_plan,
        status=filter_status, review_status=filter_review_status,
        keyword=keyword, role=user_role,
    )

    def fetch_and_serialize():
        properties = crud_property.get_properties(
            db, skip=skip, limit=limit, region=region, floor_plan=floor_plan,
            review_status=filter_review_status, status=filter_status, keyword=keyword,
        )
        total = crud_property.count_properties(
            db, region=region, floor_plan=floor_plan,
            review_status=filter_review_status, status=filter_status, keyword=keyword,
        )
        items = [Property.model_validate(p).model_dump(mode='json') for p in properties]
        return {"items": items, "total": total}

    return cache_manager.get_or_set(
        cache_key,
        fetch_and_serialize,
        ttl=settings.CACHE_SHORT_TTL,
    )


@router.get("/my", response_model=PaginatedResponse)
def list_my_properties(
    skip: int = 0,
    limit: int = 20,
    region: Optional[str] = None,
    floor_plan: Optional[str] = None,
    review_status: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_landlord),
):
    properties = crud_property.get_properties(
        db,
        skip=skip,
        limit=limit,
        region=region,
        floor_plan=floor_plan,
        owner_id=current_user.id,
        review_status=review_status,
        status=status,
    )
    total = crud_property.count_properties(
        db,
        region=region,
        floor_plan=floor_plan,
        owner_id=current_user.id,
        review_status=review_status,
        status=status,
    )
    items = [Property.model_validate(p).model_dump(mode='json') for p in properties]
    return {"items": items, "total": total}


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
    invalidate_property_cache()
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

    # 增量浏览量
    _increment_view(db, db_property)

    return db_property


def _increment_view(db: Session, db_property):
    """增加房源浏览量，失败不阻断请求"""
    try:
        db_property.view_count = (db_property.view_count or 0) + 1
        db.commit()
        db.refresh(db_property)
    except Exception:
        db.rollback()


@router.put("/{property_id}", response_model=Property)
def update_property(
    property_id: int,
    property_in: PropertyUpdate,
    background_tasks: BackgroundTasks,
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
    update_data = property_in.model_dump(exclude_unset=True)
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
        if property_status == PropertyStatus.RENTED:
            # 已出租：只能修改描述
            allowed_fields = {"description"}
            disallowed = modified_fields - allowed_fields
            if disallowed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot modify fields when property is rented. Only description can be updated."
                )
        else:
            # published/unpublished：检查是否修改了核心字段
            core_fields_modified = modified_fields & CORE_PROPERTY_FIELDS
            if core_fields_modified:
                # 修改了核心字段，标记需要修改审核状态
                needs_review_status_change = True
    elif review_status == PropertyReviewStatus.REJECTED:
        # 被拒绝：可以自由修改，准备重新提交
        pass
    
    # 在权限检查之前，将系统自动的 review_status 和 status 修改加入 update_data
    if needs_review_status_change:
        update_data["review_status"] = PropertyReviewStatus.PENDING.value
        update_data["status"] = PropertyStatus.UNPUBLISHED.value
        update_data["submitted_at"] = datetime.utcnow()
        update_data["unpublished_at"] = datetime.utcnow()
        update_data["approved_at"] = None
        update_data["published_at"] = None
    
    # 房东不能手动修改审核状态（系统自动修改的除外）
    if "review_status" in modified_fields and current_user.role != "admin" and not needs_review_status_change:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can update review status")
    
    # 房东不能通过更新接口直接修改房源运营状态（需使用专用端点）
    if "status" in modified_fields and current_user.role != "admin" and not needs_review_status_change:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot update status directly. Use the status change endpoint instead.")
    
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

    if needs_review_status_change:
        admins = db.query(User).filter(User.role == "admin", User.is_active == True).all()
        if admins:
            notification_content = f"房东「{current_user.full_name or current_user.username}」修改了房源「{updated.title}」的核心信息，需要重新审核。"
            admin_unread = {}
            for admin in admins:
                notification = MessageModel(
                    from_user_id=current_user.id,
                    to_user_id=admin.id,
                    property_id=updated.id,
                    content=notification_content,
                    message_type="notification",
                    link="/admin/properties",
                )
                db.add(notification)
                admin_unread[admin.id] = crud_message.get_unread_count(db, user_id=admin.id)

            db.commit()

            async def notify_admins():
                for admin in admins:
                    payload = {
                        "type": "new_message",
                        "message": {
                            "from_user_id": current_user.id,
                            "to_user_id": admin.id,
                            "content": notification_content,
                            "message_type": "notification",
                            "property_id": updated.id,
                            "is_read": False,
                        },
                        "unread_count": admin_unread.get(admin.id, 0) + 1,
                    }
                    await ws_manager.send_personal(payload, admin.id)

            background_tasks.add_task(notify_admins)

    invalidate_property_cache(property_id)
    return updated


@router.put("/{property_id}/review", response_model=Property)
def review_property(
    property_id: int,
    review_in: PropertyReview,
    background_tasks: BackgroundTasks,
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
    review_status_cn = {
        "approved": "已通过",
        "rejected": "已拒绝",
        "pending": "待审核",
        "reviewing": "审核中",
    }.get(updated.review_status, updated.review_status)

    notification_content = (
        f"您的房源「{updated.title}」审核状态已更新为「{review_status_cn}」。"
        f"{'审核意见：' + review_in.comment if review_in.comment else ''}"
    )
    notification = MessageModel(
        from_user_id=current_user.id,
        to_user_id=updated.owner_id,
        property_id=updated.id,
        content=notification_content,
        message_type="notification",
        link="/landlord/properties",
    )
    db.add(notification)
    db.flush()
    db.refresh(notification)
    db.commit()

    unread_before = crud_message.get_unread_count(db, user_id=updated.owner_id)

    async def notify_owner():
        payload = {
            "type": "new_message",
            "message": {
                "id": notification.id,
                "from_user_id": notification.from_user_id,
                "to_user_id": notification.to_user_id,
                "content": notification.content,
                "message_type": notification.message_type,
                "property_id": notification.property_id,
                "link": "/landlord/properties",
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat() + 'Z' if notification.created_at else None,
            },
            "unread_count": unread_before + 1,
        }
        await ws_manager.send_personal(payload, notification.to_user_id)

    background_tasks.add_task(notify_owner)

    invalidate_property_cache(property_id)
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
    if status_in.status not in {PropertyStatus.PUBLISHED, PropertyStatus.RENTED}:
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
    invalidate_property_cache(property_id)
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
    invalidate_property_cache(property_id)
    return removed


@router.post("/{property_id}/submit-review", response_model=Property)
def submit_for_review(property_id: int, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_landlord)):
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

    admins = db.query(User).filter(User.role == "admin", User.is_active == True).all()
    if admins:
        notification_content = f"房东「{current_user.full_name or current_user.username}」提交了房源「{updated.title}」审核申请，请及时处理。"
        admin_unread = {}
        for admin in admins:
            notification = MessageModel(
                from_user_id=current_user.id,
                to_user_id=admin.id,
                property_id=updated.id,
                content=notification_content,
                message_type="notification",
                link="/admin/properties",
            )
            db.add(notification)
            admin_unread[admin.id] = crud_message.get_unread_count(db, user_id=admin.id)

        db.commit()

        async def notify_admins():
            for admin in admins:
                payload = {
                    "type": "new_message",
                    "message": {
                        "from_user_id": current_user.id,
                        "to_user_id": admin.id,
                        "content": notification_content,
                        "message_type": "notification",
                        "property_id": updated.id,
                        "link": "/admin/properties",
                        "is_read": False,
                    },
                    "unread_count": admin_unread.get(admin.id, 0) + 1,
                }
                await ws_manager.send_personal(payload, admin.id)

        background_tasks.add_task(notify_admins)

    invalidate_property_cache(property_id)
    return updated


@router.post("/{property_id}/withdraw-review", response_model=Property)
def withdraw_review(property_id: int, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_landlord)):
    """房东撤销审核申请（在未审核通过前可撤回，变回草稿状态）"""
    db_property = crud_property.get_property(db, property_id=property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if db_property.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    try:
        updated = crud_property.withdraw_review(db, db_property)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="withdraw_review",
        target_type="property",
        target_id=updated.id,
        detail="Property review withdrawn by landlord, back to draft",
        ip_address=ip_address,
    )

    admins = db.query(User).filter(User.role == "admin", User.is_active == True).all()
    if admins:
        notification_content = f"房东「{current_user.full_name or current_user.username}」撤销了房源「{updated.title}」的审核申请。"
        admin_unread = {}
        for admin in admins:
            notification = MessageModel(
                from_user_id=current_user.id,
                to_user_id=admin.id,
                property_id=updated.id,
                content=notification_content,
                message_type="notification",
                link="/admin/properties",
            )
            db.add(notification)
            admin_unread[admin.id] = crud_message.get_unread_count(db, user_id=admin.id)

        db.commit()

        async def notify_admins():
            for admin in admins:
                payload = {
                    "type": "new_message",
                    "message": {
                        "from_user_id": current_user.id,
                        "to_user_id": admin.id,
                        "content": notification_content,
                        "message_type": "notification",
                        "property_id": updated.id,
                        "link": "/admin/properties",
                        "is_read": False,
                    },
                    "unread_count": admin_unread.get(admin.id, 0) + 1,
                }
                await ws_manager.send_personal(payload, admin.id)

        background_tasks.add_task(notify_admins)

    invalidate_property_cache(property_id)
    return updated


@router.post("/{property_id}/unpublish", response_model=Property)
def unpublish_property(
    property_id: int,
    background_tasks: BackgroundTasks,
    request: Request,
    data: Optional[dict] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """暂停发布房源（房东或管理员均可操作）"""
    db_property = crud_property.get_property(db, property_id=property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    
    is_admin_action = False
    admin_reason = ""
    # 权限检查：房东只能操作自己的房源，管理员可以操作所有
    if current_user.role == "admin":
        reason = data.get("reason", "") if data else ""
        is_admin_action = True
        admin_reason = reason
        try:
            updated = crud_property.admin_unpublish_property(db, db_property, reason=reason)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    elif db_property.owner_id == current_user.id:
        reason = "房东主动取消发布"
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

    if is_admin_action:
        content = f"您的房源「{updated.title}」已被管理员下架。{'原因：' + admin_reason if admin_reason else ''}"
        notification = MessageModel(
            from_user_id=current_user.id,
            to_user_id=updated.owner_id,
            property_id=updated.id,
            content=content,
            message_type="notification",
            link="/landlord/properties",
        )
        db.add(notification)
        db.commit()

        unread_before = crud_message.get_unread_count(db, user_id=updated.owner_id)

        async def notify_owner():
            payload = {
                "type": "new_message",
                "message": {
                    "from_user_id": current_user.id,
                    "to_user_id": updated.owner_id,
                    "content": content,
                    "message_type": "notification",
                    "property_id": updated.id,
                    "link": "/landlord/properties",
                    "is_read": False,
                },
                "unread_count": unread_before + 1,
            }
            await ws_manager.send_personal(payload, updated.owner_id)

        background_tasks.add_task(notify_owner)

    invalidate_property_cache(property_id)
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
    invalidate_property_cache(property_id)
    return updated
