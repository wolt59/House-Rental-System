from typing import List, Optional

from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session

from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageCreate


def get_message(db: Session, message_id: int) -> Optional[Message]:
    return db.query(Message).filter(Message.id == message_id).first()


def get_messages_received(
    db: Session,
    to_user_id: int,
    is_read: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
    message_types: Optional[List[str]] = None,
) -> List[Message]:
    query = db.query(Message).filter(Message.to_user_id == to_user_id)
    if is_read is not None:
        query = query.filter(Message.is_read == is_read)
    if message_types:
        query = query.filter(Message.message_type.in_(message_types))
    return query.order_by(Message.created_at.desc()).offset(skip).limit(limit).all()


def get_messages_sent(
    db: Session,
    from_user_id: int,
    skip: int = 0,
    limit: int = 20,
) -> List[Message]:
    return (
        db.query(Message)
        .filter(Message.from_user_id == from_user_id)
        .order_by(Message.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def count_messages_received(
    db: Session,
    to_user_id: int,
    is_read: Optional[bool] = None,
    message_types: Optional[List[str]] = None,
) -> int:
    query = db.query(Message).filter(Message.to_user_id == to_user_id)
    if is_read is not None:
        query = query.filter(Message.is_read == is_read)
    if message_types:
        query = query.filter(Message.message_type.in_(message_types))
    return query.count()


def count_messages_sent(
    db: Session,
    from_user_id: int,
) -> int:
    return db.query(Message).filter(Message.from_user_id == from_user_id).count()


def create_message(db: Session, from_user_id: int, message_in: MessageCreate) -> Message:
    message = Message(
        from_user_id=from_user_id,
        to_user_id=message_in.to_user_id,
        property_id=message_in.property_id,
        message_type=message_in.message_type or "text",
        content=message_in.content,
        link=message_in.link,
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


def mark_conversation_read(db: Session, user_id: int, peer_user_id: int) -> int:
    affected = (
        db.query(Message)
        .filter(
            Message.to_user_id == user_id,
            Message.from_user_id == peer_user_id,
            Message.is_read == False,
        )
        .update({Message.is_read: True})
    )
    db.commit()
    return affected


def get_unread_count(db: Session, user_id: int, message_type: Optional[str] = None) -> int:
    query = db.query(func.count(Message.id)).filter(
        Message.to_user_id == user_id, Message.is_read == False
    )
    if message_type == "chat":
        query = query.filter(Message.message_type.notin_(["system", "notification"]))
    elif message_type == "notification":
        query = query.filter(Message.message_type.in_(["system", "notification"]))
    return query.scalar()


def get_conversations(db: Session, user_id: int) -> List[dict]:
    contact_ids_subq = (
        db.query(Message.from_user_id)
        .filter(Message.to_user_id == user_id)
        .union(
            db.query(Message.to_user_id).filter(Message.from_user_id == user_id)
        )
        .subquery()
    )
    contacts = db.query(contact_ids_subq).distinct().all()
    contact_ids = [row[0] for row in contacts]

    if not contact_ids:
        return {"conversations": [], "total_unread": 0}

    last_msg_subq = (
        db.query(
            Message.id,
            func.greatest(Message.from_user_id, Message.to_user_id).label("uid_a"),
            func.least(Message.from_user_id, Message.to_user_id).label("uid_b"),
            func.row_number()
            .over(
                partition_by=[
                    func.greatest(Message.from_user_id, Message.to_user_id),
                    func.least(Message.from_user_id, Message.to_user_id),
                ],
                order_by=Message.created_at.desc(),
            )
            .label("rn"),
        )
        .filter(
            or_(
                Message.from_user_id == user_id,
                Message.to_user_id == user_id,
            ),
            Message.message_type.notin_(["system", "notification"]),
        )
        .subquery()
    )

    last_msgs = (
        db.query(Message)
        .join(last_msg_subq, Message.id == last_msg_subq.c.id)
        .filter(last_msg_subq.c.rn == 1)
        .order_by(Message.created_at.desc())
        .all()
    )

    conversation_map = {}
    for msg in last_msgs:
        peer_id = msg.from_user_id if msg.to_user_id == user_id else msg.to_user_id
        conversation_map[peer_id] = msg

    sorted_peers = sorted(
        conversation_map.keys(),
        key=lambda pid: conversation_map[pid].created_at,
        reverse=True,
    )

    users_map = {}
    if sorted_peers:
        db_users = db.query(User).filter(User.id.in_(sorted_peers)).all()
        users_map = {u.id: u for u in db_users}

    unread_subq = (
        db.query(
            Message.from_user_id,
            func.count(Message.id).label("cnt"),
        )
        .filter(
            Message.to_user_id == user_id,
            Message.is_read == False,
            Message.from_user_id.in_(sorted_peers),
        )
        .group_by(Message.from_user_id)
        .all()
    )
    unread_map = {row[0]: row[1] for row in unread_subq}

    result = []
    for peer_id in sorted_peers:
        msg = conversation_map[peer_id]
        peer = users_map.get(peer_id)
        content_preview = msg.content[:80] if msg.content else ""
        result.append(
            {
                "participant": {
                    "id": peer.id if peer else peer_id,
                    "username": peer.username if peer else f"用户#{peer_id}",
                    "full_name": peer.full_name if peer else None,
                    "avatar_url": peer.avatar_url if peer else None,
                },
                "last_message": content_preview,
                "last_message_time": msg.created_at,
                "last_message_type": msg.message_type,
                "unread_count": unread_map.get(peer_id, 0),
                "property_id": msg.property_id,
            }
        )

    total_unread = sum(item["unread_count"] for item in result)
    return {"conversations": result, "total_unread": total_unread}


def get_conversation_messages(
    db: Session,
    user_id: int,
    peer_user_id: int,
    skip: int = 0,
    limit: int = 50,
) -> List[Message]:
    return (
        db.query(Message)
        .filter(
            or_(
                and_(Message.from_user_id == user_id, Message.to_user_id == peer_user_id),
                and_(Message.from_user_id == peer_user_id, Message.to_user_id == user_id),
            ),
            Message.message_type.notin_(["system", "notification"]),
        )
        .order_by(Message.created_at.asc())
        .offset(skip).limit(limit).all()
    )


def search_users(db: Session, keyword: str, current_user_id: int, limit: int = 20) -> List[User]:
    return (
        db.query(User)
        .filter(
            User.id != current_user_id,
            User.is_active == True,
            or_(
                User.username.ilike(f"%{keyword}%"),
                User.full_name.ilike(f"%{keyword}%"),
            ),
        )
        .limit(limit)
        .all()
    )