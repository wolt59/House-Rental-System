from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_active_admin, get_db
from app.crud import crud_audit, crud_news
from app.schemas.news import News as NewsSchema, NewsCreate, NewsUpdate

router = APIRouter()


@router.post("/", response_model=NewsSchema, status_code=status.HTTP_201_CREATED)
def create_news(news_in: NewsCreate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    if current_user.role not in ("landlord", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only landlords and admins can create news")
    news = crud_news.create_news(db, author_id=current_user.id, news_in=news_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="create_news",
        target_type="news",
        target_id=news.id,
        detail=f"News created: {news.title}",
        ip_address=ip_address,
    )
    return news


@router.get("/", response_model=List[NewsSchema])
def list_news(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    filter_status = status or "published"
    return crud_news.get_news_list(db, status=filter_status, skip=skip, limit=limit)


@router.get("/my", response_model=List[NewsSchema])
def list_my_news(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return crud_news.get_news_list(db, author_id=current_user.id, skip=skip, limit=limit)


@router.get("/{news_id}", response_model=NewsSchema)
def read_news(news_id: int, db: Session = Depends(get_db)):
    news = crud_news.get_news(db, news_id)
    if not news:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")
    return news


@router.put("/{news_id}", response_model=NewsSchema)
def update_news(news_id: int, news_in: NewsUpdate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    news = crud_news.get_news(db, news_id)
    if not news:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found")
    if news.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    updated = crud_news.update_news(db, news, news_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_news",
        target_type="news",
        target_id=updated.id,
        detail=f"News updated: {updated.title}",
        ip_address=ip_address,
    )
    return updated


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
    return None
