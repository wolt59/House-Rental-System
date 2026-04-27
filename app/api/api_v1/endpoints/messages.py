from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.crud import crud_message
from app.models.property import Property
from app.schemas.message import Message as MessageSchema, MessageCreate

router = APIRouter()


@router.post("/", response_model=MessageSchema, status_code=status.HTTP_201_CREATED)
def send_message(message_in: MessageCreate, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    if message_in.property_id:
        property_obj = db.query(Property).filter(Property.id == message_in.property_id).first()
        if not property_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    return crud_message.create_message(db, from_user_id=current_user.id, message_in=message_in)


@router.get("/received", response_model=List[MessageSchema])
def list_received_messages(
    unread: Optional[bool] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    is_read = None if unread is None else not unread
    return crud_message.get_messages_received(db, to_user_id=current_user.id, is_read=is_read, skip=skip, limit=limit)


@router.get("/sent", response_model=List[MessageSchema])
def list_sent_messages(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return crud_message.get_messages_sent(db, from_user_id=current_user.id, skip=skip, limit=limit)


@router.put("/{message_id}/read", response_model=MessageSchema)
def mark_message_read(message_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    message = crud_message.get_message(db, message_id)
    if not message or message.to_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return crud_message.mark_message_read(db, message)
