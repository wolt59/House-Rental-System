from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, constr, validator

from app.schemas.common import UTCDatetimeModel


class UserBase(BaseModel):
    username: constr(min_length=3, max_length=80)
    email: EmailStr
    phone: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = "tenant"

    @validator("phone", "full_name", pre=True)
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v


class UserCreate(UserBase):
    password: constr(min_length=8)


class UserUpdate(BaseModel):
    phone: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    id_card_number: Optional[str] = None
    role: Optional[str] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: constr(min_length=8)


class UserInDBBase(UserBase, UTCDatetimeModel):
    id: int
    avatar_url: Optional[str] = None
    is_active: bool
    id_card_number: Optional[str] = None  # 添加身份证号码字段
    remark: Optional[str] = None  # 添加备注字段
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class User(UserInDBBase):
    pass


class LandlordPropertyStats(BaseModel):
    owner_id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    total_properties: int
    approved_properties: int
    pending_properties: int
    rejected_properties: int
    vacant_properties: int
    rented_properties: int
    maintenance_properties: int

    class Config:
        from_attributes = True


class UserInDB(UserInDBBase):
    hashed_password: str
