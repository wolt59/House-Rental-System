from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_active_admin, get_db
from app.cache import cache_manager, CacheKey, invalidate_news_cache
from app.core.config import settings
from app.crud import crud_audit, crud_news
from app.schemas.news import News as NewsSchema, NewsCreate, NewsUpdate, NewsReview

router = APIRouter()


def _news_to_schema(news) -> dict:
    """将 News 模型转为包含 author_name 的字典"""
    d = {
        "id": news.id,
        "author_id": news.author_id,
        "title": news.title,
        "content": news.content,
        "category": news.category,
        "cover_image": news.cover_image,
        "status": news.status,
        "review_message": news.review_message,
        "view_count": news.view_count,
        "published_at": news.published_at,
        "created_at": news.created_at,
        "updated_at": news.updated_at,
        "author_name": news.author.full_name or news.author.username if news.author else None,
    }
    return d


@router.post("/", response_model=NewsSchema, status_code=status.HTTP_201_CREATED)
def create_news(news_in: NewsCreate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    """房东/管理员发布新闻，draft=存草稿，published=立即发布（租客可见）"""
    if current_user.role not in ("landlord", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only landlords and admins can create news")
    if news_in.status not in ("draft", "published"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="status must be 'draft' or 'published'")
    news = crud_news.create_news(db, author_id=current_user.id, news_in=news_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="create_news",
        target_type="news",
        target_id=news.id,
        detail=f"News created: {news.title} (status={news.status})",
        ip_address=ip_address,
    )
    if news.status == "published":
        invalidate_news_cache()
    return _news_to_schema(news)


@router.get("/", response_model=Dict[str, Any])
def list_news(
    status: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """公开列表：只展示已发布(published)的新闻"""
    filter_status = status or "published"
    cache_key = CacheKey.news_list(status=filter_status, category=category, skip=skip, limit=limit)
    return cache_manager.get_or_set(
        cache_key,
        lambda: _fetch_news_list(db, filter_status, category, skip, limit),
        ttl=settings.CACHE_SHORT_TTL,
    )


def _fetch_news_list(db: Session, status: str, category: Optional[str], skip: int, limit: int) -> dict:
    items, total = crud_news.get_news_list(db, status=status, category=category, skip=skip, limit=limit)
    return {
        "items": [_news_to_schema(n) for n in items],
        "total": total,
    }


@router.get("/my", response_model=Dict[str, Any])
def list_my_news(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """当前用户（房东/管理员）的新闻列表，包含所有状态"""
    items, total = crud_news.get_news_list(db, author_id=current_user.id, skip=skip, limit=limit)
    return {
        "items": [_news_to_schema(n) for n in items],
        "total": total,
    }


@router.get("/all", response_model=Dict[str, Any])
def list_all_news_admin(
    status: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_admin),
):
    """管理员：获取全部新闻（含所有状态）"""
    items, total = crud_news.get_all_news_admin(db, status=status, category=category, skip=skip, limit=limit)
    return {
        "items": [_news_to_schema(n) for n in items],
        "total": total,
    }


@router.get("/{news_id}", response_model=NewsSchema)
def read_news(news_id: int, db: Session = Depends(get_db)):
    news = crud_news.get_news(db, news_id)
    if not news:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")
    crud_news.increment_view_count(db, news)
    return _news_to_schema(news)


@router.put("/{news_id}", response_model=NewsSchema)
def update_news(news_id: int, news_in: NewsUpdate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    """房东/管理员更新新闻"""
    news = crud_news.get_news(db, news_id)
    if not news:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")
    if news.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if news_in.status is not None and news_in.status not in ("draft", "published"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="status must be 'draft' or 'published'")
    # 清除之前的审核意见（如果重新发布）
    if news_in.status == "published" and news.status == "rejected":
        news.review_message = None
    updated = crud_news.update_news(db, news, news_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_news",
        target_type="news",
        target_id=updated.id,
        detail=f"News updated: {updated.title} (status={updated.status})",
        ip_address=ip_address,
    )
    invalidate_news_cache(news_id)
    return _news_to_schema(updated)


@router.post("/{news_id}/review", response_model=NewsSchema)
def review_news(news_id: int, review_in: NewsReview, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_admin)):
    """
    管理员审核（事后审核）：
    - action='reject' (下架): published → rejected，必须填写原因
    - action='approve' (恢复): rejected → published
    """
    news = crud_news.get_news(db, news_id)
    if not news:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")
    if review_in.action not in ("approve", "reject"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="action must be 'approve' or 'reject'")
    if review_in.action == "reject":
        if news.status != "published":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only published news can be rejected")
        if not review_in.message:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rejection requires a message")
    elif review_in.action == "approve":
        if news.status != "rejected":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only rejected news can be re-approved")
    updated = crud_news.review_news(db, news, review_in.action, review_in.message)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action=f"review_{review_in.action}_news",
        target_type="news",
        target_id=updated.id,
        detail=f"News {review_in.action}d: {updated.title}" + (f" - {review_in.message}" if review_in.message else ""),
        ip_address=ip_address,
    )
    invalidate_news_cache(news_id)
    return _news_to_schema(updated)


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_news(news_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    news = crud_news.get_news(db, news_id)
    if not news:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")
    if news.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    crud_news.delete_news(db, news)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="delete_news",
        target_type="news",
        target_id=news_id,
        detail=f"News deleted: {news.title}",
        ip_address=ip_address,
    )
    invalidate_news_cache(news_id)
    return None
