from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.api.websocket import ws_manager
from app.crud import crud_message
from app.models.property import Property
from app.schemas.message import (
    Message as MessageSchema,
    MessageCreate,
    ConversationListResponse,
    UnreadCountResponse,
    UserSearchResult,
)

router = APIRouter()


@router.post("/", response_model=MessageSchema, status_code=status.HTTP_201_CREATED)
def send_message(
    message_in: MessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    if message_in.to_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send message to yourself",
        )
    if message_in.property_id:
        property_obj = db.query(Property).filter(Property.id == message_in.property_id).first()
        if not property_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    message = crud_message.create_message(db, from_user_id=current_user.id, message_in=message_in)

    unread_before = crud_message.get_unread_count(db, user_id=message_in.to_user_id)

    async def notify_recipient():
        payload = {
            "type": "new_message",
            "message": {
                "id": message.id,
                "from_user_id": message.from_user_id,
                "to_user_id": message.to_user_id,
                "content": message.content,
                "message_type": message.message_type,
                "property_id": message.property_id,
                "link": message.link,
                "is_read": message.is_read,
                "created_at": message.created_at.isoformat() + 'Z' if message.created_at else None,
            },
            "unread_count": unread_before + 1,
        }
        await ws_manager.send_personal(payload, message.to_user_id)

    background_tasks.add_task(notify_recipient)
    return message


@router.get("/received", response_model=List[MessageSchema])
def list_received_messages(
    unread: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
    type: Optional[str] = Query(None, description="Filter by message type: system,notification (comma separated)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    is_read = None if unread is None else not unread
    message_types = [t.strip() for t in type.split(",") if t.strip()] if type else None
    return crud_message.get_messages_received(
        db, to_user_id=current_user.id, is_read=is_read, skip=skip, limit=limit, message_types=message_types,
    )


@router.get("/sent", response_model=List[MessageSchema])
def list_sent_messages(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return crud_message.get_messages_sent(db, from_user_id=current_user.id, skip=skip, limit=limit)


@router.put("/{message_id}/read", response_model=MessageSchema)
def mark_message_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    message = crud_message.get_message(db, message_id)
    if not message or message.to_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return crud_message.mark_message_read(db, message)


@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return crud_message.get_conversations(db, user_id=current_user.id)


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    type: Optional[str] = Query(None, description="Filter by type: chat, notification, or all"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    count = crud_message.get_unread_count(db, user_id=current_user.id, message_type=type)
    return {"total_unread": count}


@router.get("/conversations/{peer_user_id}", response_model=List[MessageSchema])
def get_conversation_messages(
    peer_user_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    if peer_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation participant",
        )
    messages = crud_message.get_conversation_messages(
        db, user_id=current_user.id, peer_user_id=peer_user_id, skip=skip, limit=limit
    )
    return messages


@router.put("/conversations/{peer_user_id}/read")
def mark_conversation_read(
    peer_user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    if peer_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation participant",
        )
    affected = crud_message.mark_conversation_read(
        db, user_id=current_user.id, peer_user_id=peer_user_id
    )
    return {"marked_read": affected}


@router.get("/users/search", response_model=List[UserSearchResult])
def search_users(
    keyword: str = Query(..., min_length=1, description="Search keyword for username or full name"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    if len(keyword.strip()) < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Keyword too short")
    return crud_message.search_users(
        db, keyword=keyword.strip(), current_user_id=current_user.id, limit=limit
    )