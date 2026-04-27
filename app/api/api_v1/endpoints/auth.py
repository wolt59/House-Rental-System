from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.crud import crud_user, crud_audit
from app.schemas.user import UserCreate, User

router = APIRouter()


@router.post("/register", response_model=User)
def register(user_in: UserCreate, request: Request, db: Session = Depends(get_db)):
    existing = crud_user.get_user_by_username(db, user_in.username) or crud_user.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already registered")
    user = crud_user.create_user(db, user_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=user.id,
        action="user_register",
        target_type="user",
        target_id=user.id,
        detail="New user registered",
        ip_address=ip_address,
    )
    return user


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None, db: Session = Depends(get_db)):
    user = crud_user.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    ip_address = request.client.host if request and request.client else None
    user.last_login_at = datetime.utcnow()
    user.last_login_ip = ip_address
    db.commit()

    crud_audit.create_audit_log(
        db,
        user_id=user.id,
        action="user_login",
        target_type="user",
        target_id=user.id,
        detail="User login successful",
        ip_address=ip_address,
    )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
