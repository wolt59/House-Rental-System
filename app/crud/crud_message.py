from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.message import Message
from app.schemas.message import MessageCreate


def get_message(db: Session, message_id: int) -> Optional[Message]:
    return db.query(Message).filter(Message.id == message_id).first()


def get_messages_received(
    db: Session,
    to_user_id: int,
    is_read: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[Message]:
    query = db.query(Message).filter(Message.to_user_id == to_user_id)
    if is_read is not None:
        query = query.filter(Message.is_read == is_read)
    return query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()


def get_messages_sent(
    db: Session,
    from_user_id: int,
    skip: int = 0,
    limit: int = 20,
) -> List[Message]:
    return db.query(Message).filter(Message.from_user_id == from_user_id).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()


def create_message(db: Session, from_user_id: int, message_in: MessageCreate) -> Message:
    message = Message(
        from_user_id=from_user_id,
        to_user_id=message_in.to_user_id,
        property_id=message_in.property_id,
        message_type=message_in.message_type or "text",
        content=message_in.content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def mark_message_read(db: Session, db_message: Message) -> Message:
    db_message.is_read = True
    db.commit()
    db.refresh(db_message)
    return db_message
