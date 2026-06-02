from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.news import News
from app.models.user import User
from app.schemas.news import NewsCreate, NewsUpdate


def get_news(db: Session, news_id: int) -> Optional[News]:
    return db.query(News).options(joinedload(News.author)).filter(News.id == news_id).first()


def get_news_list(
    db: Session,
    status: Optional[str] = None,
    author_id: Optional[int] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[News], int]:
    query = db.query(News)
    if status is not None:
        query = query.filter(News.status == status)
    if author_id is not None:
        query = query.filter(News.author_id == author_id)
    if category is not None:
        query = query.filter(News.category == category)
    total = query.count()
    items = query.options(joinedload(News.author)).order_by(News.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def get_all_news_admin(
    db: Session,
    status: Optional[str] = None,
    author_id: Optional[int] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[News], int]:
    """管理员获取所有新闻（包括各种状态）"""
    query = db.query(News)
    if status is not None:
        query = query.filter(News.status == status)
    if author_id is not None:
        query = query.filter(News.author_id == author_id)
    if category is not None:
        query = query.filter(News.category == category)
    total = query.count()
    items = query.options(joinedload(News.author)).order_by(News.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def create_news(db: Session, author_id: int, news_in: NewsCreate) -> News:
    news = News(
        author_id=author_id,
        title=news_in.title,
        content=news_in.content,
        category=news_in.category,
        cover_image=news_in.cover_image,
        status=news_in.status or "draft",
        published_at=datetime.utcnow() if news_in.status == "published" else None,
    )
    db.add(news)
    db.commit()
    db.refresh(news)
    return news


def update_news(db: Session, db_news: News, news_in: NewsUpdate) -> News:
    update_data = news_in.dict(exclude_unset=True)
    if news_in.status == "published" and db_news.status != "published":
        update_data["published_at"] = datetime.utcnow()
    for field, value in update_data.items():
        setattr(db_news, field, value)
    db.commit()
    db.refresh(db_news)
    return db_news


def review_news(db: Session, db_news: News, action: str, message: Optional[str] = None) -> News:
    """管理员审核（事后审核）：approve=恢复发布, reject=下架"""
    if action == "approve":
        db_news.status = "published"
        db_news.published_at = db_news.published_at or datetime.utcnow()
        db_news.review_message = None
    elif action == "reject":
        db_news.status = "rejected"
        db_news.review_message = message
    db.commit()
    db.refresh(db_news)
    return db_news



def increment_view_count(db: Session, db_news: News) -> News:
    db_news.view_count = (db_news.view_count or 0) + 1
    db.commit()
    db.refresh(db_news)
    return db_news


def delete_news(db: Session, db_news: News) -> News:
    db.delete(db_news)
    db.commit()
    return db_news
