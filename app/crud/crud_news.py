from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.news import News
from app.schemas.news import NewsCreate, NewsUpdate


def get_news(db: Session, news_id: int) -> Optional[News]:
    return db.query(News).filter(News.id == news_id).first()


def get_news_list(
    db: Session,
    status: Optional[str] = None,
    author_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[News]:
    query = db.query(News)
    if status is not None:
        query = query.filter(News.status == status)
    if author_id is not None:
        query = query.filter(News.author_id == author_id)
    return query.order_by(News.created_at.desc()).offset(skip).limit(limit).all()


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


def delete_news(db: Session, db_news: News) -> News:
    db.delete(db_news)
    db.commit()
    return db_news
