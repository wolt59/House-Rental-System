from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_user_optional, get_db
from app.core.enums import PropertyReviewStatus, PropertyStatus
from app.crud import crud_property_favorite, crud_audit
from app.models.property import Property
from app.models.property_favorite import PropertyComment
from app.schemas.property_favorite import (
    PropertyComment as PropertyCommentSchema,
    PropertyCommentCreate,
    PropertyCommentUpdate,
    PropertyFavoriteToggleResponse,
)

router = APIRouter(prefix="/property-interactions", tags=["property_interactions"])


# ====================================================================
#  房源摘要（详情页用：返回当前用户是否收藏、收藏数、评论数）
# ====================================================================

@router.get("/properties/{property_id}/summary")
def get_property_interaction_summary(
    property_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """获取当前房源的收藏数、评论数，以及当前用户是否已收藏。

    可见性策略与 `read_property` 保持一致：
    - 已审核通过 + published：任何人可访问
    - 已审核通过 + 非 published：仅房东本人/管理员可访问
    - 未审核通过：仅房东本人/管理员可访问
    未登录用户 `is_favorited` 始终为 False。
    """
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    is_owner = current_user is not None and prop.owner_id == current_user.id
    is_admin = current_user is not None and current_user.role == "admin"
    if prop.review_status == PropertyReviewStatus.APPROVED:
        if prop.status != PropertyStatus.PUBLISHED and not is_owner and not is_admin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    else:
        if not is_owner and not is_admin:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    favorite_count = crud_property_favorite.count_favorites(db, property_id)
    comment_count = crud_property_favorite.count_comments(db, property_id)
    is_fav = (
        crud_property_favorite.is_favorited(db, current_user.id, property_id)
        if current_user is not None
        else False
    )
    return {
        "property_id": property_id,
        "favorite_count": favorite_count,
        "comment_count": comment_count,
        "is_favorited": is_fav,
    }


# ====================================================================
#  收藏
# ====================================================================

@router.post("/favorites/toggle", response_model=PropertyFavoriteToggleResponse)
def toggle_favorite(
    property_id: int = Query(..., description="房源 ID"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """切换收藏状态：已收藏则取消，未收藏则添加。"""
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    existing = crud_property_favorite.get_favorite(db, current_user.id, property_id)
    if existing:
        crud_property_favorite.remove_favorite(db, current_user.id, property_id)
        is_fav = False
    else:
        crud_property_favorite.add_favorite(db, current_user.id, property_id)
        is_fav = True

    favorite_count = crud_property_favorite.count_favorites(db, property_id)

    ip_address = request.client.host if request and request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action=("add_favorite" if is_fav else "remove_favorite"),
        target_type="property",
        target_id=property_id,
        detail=f"Property favorite toggled: is_favorited={is_fav}",
        ip_address=ip_address,
    )

    return {
        "property_id": property_id,
        "is_favorited": is_fav,
        "favorite_count": favorite_count,
    }


@router.get("/favorites/me")
def list_my_favorites(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """获取当前用户的收藏列表。"""
    items, total = crud_property_favorite.get_user_favorites(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    from datetime import timezone
    serialized = []
    for it in items:
        ca = it["created_at"]
        ca_iso = ca.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z") if ca else None
        serialized.append(
            {
                "id": it["id"],
                "property_id": it["property_id"],
                "user_id": it["user_id"],
                "created_at": ca_iso,
                "property_title": it["property_title"],
                "property_address": it["property_address"],
                "property_rent": it["property_rent"],
                "property_status": it["property_status"],
                "property_cover": it["property_cover"],
            }
        )
    return {"items": serialized, "total": total}


# ====================================================================
#  评论
# ====================================================================

def _serialize_comment(c: PropertyComment) -> dict:
    user = c.user
    return {
        "id": c.id,
        "property_id": c.property_id,
        "user_id": c.user_id,
        "content": c.content,
        "user_name": (user.full_name or user.username) if user else None,
        "user_avatar": user.avatar_url if user else None,
        "user_role": user.role if user else None,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }


@router.post("/comments", status_code=status.HTTP_201_CREATED)
def create_property_comment(
    comment_in: PropertyCommentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    prop = db.query(Property).filter(Property.id == comment_in.property_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")

    content = (comment_in.content or "").strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="评论内容不能为空")

    comment = crud_property_favorite.create_comment(
        db, user_id=current_user.id, property_id=comment_in.property_id, content=content
    )
    db.refresh(comment)

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="create_property_comment",
        target_type="property_comment",
        target_id=comment.id,
        detail=f"Comment created for property {comment.property_id}",
        ip_address=ip_address,
    )

    return _serialize_comment(comment)


@router.get("/properties/{property_id}/comments")
def list_property_comments(
    property_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    rows, total = crud_property_favorite.get_property_comments(
        db, property_id=property_id, skip=skip, limit=limit
    )
    items = [_serialize_comment(c) for c in rows]
    return {"items": items, "total": total}


@router.put("/comments/{comment_id}")
def update_property_comment(
    comment_id: int,
    comment_in: PropertyCommentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    comment = crud_property_favorite.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if current_user.role != "admin" and comment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改此评论")

    content = (comment_in.content or "").strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="评论内容不能为空")

    updated = crud_property_favorite.update_comment(db, comment, content)
    db.refresh(updated)

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_property_comment",
        target_type="property_comment",
        target_id=updated.id,
        detail=f"Comment updated id={updated.id}",
        ip_address=ip_address,
    )
    return _serialize_comment(updated)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property_comment(
    comment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    comment = crud_property_favorite.get_comment(db, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if current_user.role != "admin" and comment.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权删除此评论")

    crud_property_favorite.delete_comment(db, comment)

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="delete_property_comment",
        target_type="property_comment",
        target_id=comment_id,
        detail=f"Comment deleted id={comment_id}",
        ip_address=ip_address,
    )
    return None
