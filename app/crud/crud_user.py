from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_in: UserCreate):
    user = User(
        username=user_in.username,
        email=user_in.email,
        phone=user_in.phone,
        full_name=user_in.full_name,
        role=user_in.role or "tenant",
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def update_user(db: Session, db_user: User, user_in: UserUpdate):
    if user_in.phone is not None:
        db_user.phone = user_in.phone
    if user_in.full_name is not None:
        db_user.full_name = user_in.full_name
    if user_in.avatar_url is not None:
        db_user.avatar_url = user_in.avatar_url
    if user_in.id_card_number is not None:
        db_user.id_card_number = user_in.id_card_number
    if user_in.role is not None:
        db_user.role = user_in.role
    db.commit()
    db.refresh(db_user)
    return db_user
