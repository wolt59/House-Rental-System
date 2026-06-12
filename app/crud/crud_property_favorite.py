from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.property_favorite import PropertyFavorite, PropertyComment
from app.models.property import Property
from app.models.property_image import PropertyImage


# ============================================================
#  收藏
# ============================================================

def get_favorite(db: Session, user_id: int, property_id: int) -> Optional[PropertyFavorite]:
    return (
        db.query(PropertyFavorite)
        .filter(PropertyFavorite.user_id == user_id, PropertyFavorite.property_id == property_id)
        .first()
    )


def is_favorited(db: Session, user_id: int, property_id: int) -> bool:
    return (
        db.query(PropertyFavorite)
        .filter(PropertyFavorite.user_id == user_id, PropertyFavorite.property_id == property_id)
        .first()
        is not None
    )


def add_favorite(db: Session, user_id: int, property_id: int) -> PropertyFavorite:
    """若已存在则直接返回，否则新增。"""
    fav = get_favorite(db, user_id, property_id)
    if fav:
        return fav
    fav = PropertyFavorite(user_id=user_id, property_id=property_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return fav


def remove_favorite(db: Session, user_id: int, property_id: int) -> bool:
    fav = get_favorite(db, user_id, property_id)
    if not fav:
        return False
    db.delete(fav)
    db.commit()
    return True


def count_favorites(db: Session, property_id: int) -> int:
    return db.query(PropertyFavorite).filter(PropertyFavorite.property_id == property_id).count()


def get_user_favorites(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[dict], int]:
    """获取用户收藏列表，附带房源基础信息与封面图。"""
    base_query = db.query(PropertyFavorite).filter(PropertyFavorite.user_id == user_id)
    total = base_query.count()
    rows = base_query.order_by(PropertyFavorite.created_at.desc()).offset(skip).limit(limit).all()
    items: List[dict] = []
    for fav in rows:
        prop: Property = fav.property
        cover = None
        if prop and prop.images:
            cover_img = next((img for img in prop.images if img.is_cover == 1), prop.images[0])
            cover = cover_img.image_url
        items.append(
            {
                "id": fav.id,
                "property_id": fav.property_id,
                "user_id": fav.user_id,
                "created_at": fav.created_at,
                "property_title": prop.title if prop else None,
                "property_address": prop.address if prop else None,
                "property_rent": prop.rent if prop else None,
                "property_status": prop.status if prop else None,
                "property_cover": cover,
            }
        )
    return items, total


# ============================================================
#  评论
# ============================================================

def get_comment(db: Session, comment_id: int) -> Optional[PropertyComment]:
    return db.query(PropertyComment).filter(PropertyComment.id == comment_id).first()


def get_property_comments(
    db: Session,
    property_id: int,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[PropertyComment], int]:
    base_query = db.query(PropertyComment).filter(PropertyComment.property_id == property_id)
    total = base_query.count()
    rows = (
        base_query.order_by(PropertyComment.created_at.desc()).offset(skip).limit(limit).all()
    )
    return rows, total


def create_comment(
    db: Session,
    user_id: int,
    property_id: int,
    content: str,
) -> PropertyComment:
    comment = PropertyComment(user_id=user_id, property_id=property_id, content=content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def update_comment(db: Session, comment: PropertyComment, content: str) -> PropertyComment:
    comment.content = content
    db.commit()
    db.refresh(comment)
    return comment


def delete_comment(db: Session, comment: PropertyComment) -> None:
    db.delete(comment)
    db.commit()


def count_comments(db: Session, property_id: int) -> int:
    return db.query(PropertyComment).filter(PropertyComment.property_id == property_id).count()
