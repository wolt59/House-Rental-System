from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MessageBase(BaseModel):
    to_user_id: int
    property_id: Optional[int] = None
    content: str


class MessageCreate(MessageBase):
    message_type: Optional[str] = "text"


class Message(MessageBase):
    id: int
    from_user_id: int
    message_type: str
    created_at: datetime
    is_read: bool

    class Config:
        from_attributes = True
