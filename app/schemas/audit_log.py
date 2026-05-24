from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.common import UTCDatetimeModel


class AuditLog(UTCDatetimeModel):
    id: int
    user_id: Optional[int] = None
    action: str
    target_type: str
    target_id: Optional[int] = None
    detail: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
