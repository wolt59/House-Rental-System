from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, field_serializer, field_validator

from app.schemas.common import UTCDatetimeModel


class MessageBase(BaseModel):
    to_user_id: int
    property_id: Optional[int] = None
    content: str
    link: Optional[str] = None

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        if len(v) > 5000:
            raise ValueError("Message content exceeds maximum length of 5000 characters")
        return v.strip()


class MessageCreate(MessageBase):
    message_type: Optional[str] = "text"

    @field_validator("message_type")
    @classmethod
    def validate_message_type(cls, v: Optional[str]) -> str:
        allowed = {"text", "system", "notification"}
        if v and v not in allowed:
            raise ValueError(f"message_type must be one of {allowed}")
        return v or "text"


class Message(MessageBase, UTCDatetimeModel):
    id: int
    from_user_id: int
    message_type: str
    created_at: datetime
    is_read: bool

    class Config:
        from_attributes = True


class ConversationParticipant(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class ConversationSummary(BaseModel):
    participant: ConversationParticipant
    last_message: str
    last_message_time: datetime
    last_message_type: str
    unread_count: int
    property_id: Optional[int] = None

    @field_serializer('last_message_time', when_used='json')
    def serialize_datetime(self, value: datetime) -> str:
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z')
        if value is not None:
            return value.isoformat()
        return None


class ConversationListResponse(BaseModel):
    conversations: list[ConversationSummary]
    total_unread: int


class UnreadCountResponse(BaseModel):
    total_unread: int


class UserSearchResult(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str

    class Config:
        from_attributes = True