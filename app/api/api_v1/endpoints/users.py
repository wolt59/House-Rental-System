from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_admin, get_current_active_user, get_db
from app.core.security import get_password_hash
from app.crud import crud_user, crud_property, crud_audit
from app.models.user import User as UserModel
from app.schemas.user import User, UserUpdate, LandlordPropertyStats, PasswordChange

router = APIRouter()


@router.get("/", response_model=List[User])
def list_users(
    skip: int = 0,
    limit: int = 20,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_admin),
):
    query = db.query(UserModel)
    if role is not None:
        query = query.filter(UserModel.role == role)
    if is_active is not None:
        query = query.filter(UserModel.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@router.get("/me", response_model=User)
def read_current_user(current_user=Depends(get_current_active_user)):
    return current_user


@router.get("/landlord-stats", response_model=List[LandlordPropertyStats])
def list_landlord_property_stats(
    skip: int = 0,
    limit: int = 20,
    owner_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_admin),
):
    return crud_property.get_landlord_property_stats(db, skip=skip, limit=limit, owner_id=owner_id)


@router.get("/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    user = crud_user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.put("/me", response_model=User)
def update_current_user(user_in: UserUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    if user_in.role is not None and user_in.role != current_user.role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change your own role")
    updated = crud_user.update_user(db, current_user, user_in)
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_user",
        target_type="user",
        target_id=updated.id,
        detail="User updated their profile",
        ip_address=None,
    )
    return updated


@router.put("/me/password", response_model=User)
def change_password(
    password_in: PasswordChange,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    from app.core.security import verify_password
    if not verify_password(password_in.old_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password")
    current_user.hashed_password = get_password_hash(password_in.new_password)
    db.commit()
    db.refresh(current_user)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="change_password",
        target_type="user",
        target_id=current_user.id,
        detail="User changed their password",
        ip_address=ip_address,
    )
    return current_user


@router.put("/{user_id}", response_model=User)
def update_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if user_in.role is not None and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can change roles")
    user = crud_user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    updated = crud_user.update_user(db, user, user_in)
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_user",
        target_type="user",
        target_id=updated.id,
        detail="User profile updated by admin" if current_user.role == "admin" else "User updated their profile",
        ip_address=None,
    )
    return updated


@router.put("/{user_id}/status", response_model=User)
def toggle_user_status(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_admin),
):
    user = crud_user.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate yourself")
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="toggle_user_status",
        target_type="user",
        target_id=user.id,
        detail=f"User status set to {'active' if user.is_active else 'inactive'}",
        ip_address=ip_address,
    )
    return user
