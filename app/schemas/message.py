from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, field_serializer, field_validator, model_validator

from app.schemas.common import UTCDatetimeModel

# 允许的消息类型
TEXT_MESSAGE_TYPES = {"text"}
MEDIA_MESSAGE_TYPES = {"image", "file", "audio", "video"}
SYSTEM_MESSAGE_TYPES = {"system", "notification"}
ALL_MESSAGE_TYPES = TEXT_MESSAGE_TYPES | MEDIA_MESSAGE_TYPES | SYSTEM_MESSAGE_TYPES


class MessageBase(BaseModel):
    to_user_id: int
    property_id: Optional[int] = None
    content: str = ""
    link: Optional[str] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None

    @field_validator("content")
    @classmethod
    def content_within_limit(cls, v: str) -> str:
        if v is None:
            return ""
        if len(v) > 5000:
            raise ValueError("Message content exceeds maximum length of 5000 characters")
        return v


class MessageCreate(MessageBase):
    message_type: Optional[str] = "text"

    @field_validator("message_type")
    @classmethod
    def validate_message_type(cls, v: Optional[str]) -> str:
        if not v:
            return "text"
        if v not in ALL_MESSAGE_TYPES:
            raise ValueError(f"message_type must be one of {sorted(ALL_MESSAGE_TYPES)}")
        return v

    @model_validator(mode="after")
    def validate_file_payload(self):
        """非文本消息必须提供 file_url。"""
        mt = self.message_type or "text"
        if mt in MEDIA_MESSAGE_TYPES and not (self.file_url and str(self.file_url).strip()):
            raise ValueError(f"{mt} message requires file_url")
        return self


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


class ChatUploadResponse(BaseModel):
    """聊天文件上传响应"""
    url: str
    filename: str
    original_name: str
    size: int
    mime_type: str
    message_type: str  # 推断出的消息类型（image/file/audio/video）