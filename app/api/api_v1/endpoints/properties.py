from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_active_admin,
    get_current_active_landlord,
    get_current_active_user,
    get_current_user_optional,
    get_db,
)
from app.crud import crud_audit, crud_property
from app.models.message import Message as MessageModel
from app.models.property import Property as PropertyModel
from app.schemas.property import (
    Property,
    PropertyCreate,
    PropertyReview,
    PropertyStatusUpdate,
    PropertyUpdate,
)

router = APIRouter()


@router.get("/", response_model=List[Property])
def list_properties(
    skip: int = 0,
    limit: int = 20,
    region: Optional[str] = None,
    floor_plan: Optional[str] = None,
    status: Optional[str] = None,
    review_status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    is_admin = current_user and current_user.role == "admin"
    if is_admin:
        effective_review_status = review_status
    else:
        if review_status and review_status != "approved":
            effective_review_status = "approved"
        else:
            effective_review_status = review_status if review_status else "approved"
    return crud_property.get_properties(
        db,
        skip=skip,
        limit=limit,
        region=region,
        floor_plan=floor_plan,
        review_status=effective_review_status,
        status=status,
    )


@router.get("/my", response_model=List[Property])
def list_my_properties(
    skip: int = 0,
    limit: int = 20,
    region: Optional[str] = None,
    floor_plan: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_landlord),
):
    return crud_property.get_properties(
        db,
        skip=skip,
        limit=limit,
        region=region,
        floor_plan=floor_plan,
        owner_id=current_user.id,
    )


@router.get("/owner/{owner_id}", response_model=List[Property])
def list_owner_properties(
    owner_id: int,
    skip: int = 0,
    limit: int = 20,
    review_status: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_admin),
):
    return crud_property.get_properties(
        db,
        skip=skip,
        limit=limit,
        owner_id=owner_id,
        review_status=review_status,
        status=status,
    )


@router.post("/", response_model=Property, status_code=status.HTTP_201_CREATED)
def create_property(property_in: PropertyCreate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_landlord)):
    property_obj = crud_property.create_property(db, owner_id=current_user.id, property_in=property_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="create_property",
        target_type="property",
        target_id=property_obj.id,
        detail=f"Property created with pending review",
        ip_address=ip_address,
    )
    return property_obj


@router.get("/{property_id}", response_model=Property)
def read_property(property_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
    db_property = crud_property.get_property(db, property_id=property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if (
        db_property.review_status != "approved"
        and (not current_user or db_property.owner_id != current_user.id)
        and (not current_user or current_user.role != "admin")
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    db_property.view_count = (db_property.view_count or 0) + 1
    db.commit()
    db.refresh(db_property)
    return db_property


@router.put("/{property_id}", response_model=Property)
def update_property(
    property_id: int,
    property_in: PropertyUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_landlord),
):
    db_property = crud_property.get_property(db, property_id=property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if db_property.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if property_in.review_status is not None and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can update review status")
    if property_in.status is not None and current_user.role != "admin" and db_property.review_status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change occupancy status before approval")
    updated = crud_property.update_property(db, db_property, property_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_property",
        target_type="property",
        target_id=updated.id,
        detail=f"Updated property fields: {list(property_in.dict(exclude_unset=True).keys())}",
        ip_address=ip_address,
    )
    return updated


@router.put("/{property_id}/review", response_model=Property)
def review_property(
    property_id: int,
    review_in: PropertyReview,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_admin),
):
    db_property = crud_property.get_property(db, property_id=property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if review_in.review_status not in {"approved", "rejected"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review status must be approved or rejected")
    db_property.review_status = review_in.review_status
    db.commit()
    db.refresh(db_property)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="review_property",
        target_type="property",
        target_id=db_property.id,
        detail=f"Review status set to {review_in.review_status}. Comment: {review_in.comment or 'none'}",
        ip_address=ip_address,
    )
    notification_content = (
        f"Your property '{db_property.title}' review status is now '{review_in.review_status}'. "
        f"Comment: {review_in.comment or 'none'}."
    )
    notification = MessageModel(
        from_user_id=current_user.id,
        to_user_id=db_property.owner_id,
        property_id=db_property.id,
        content=notification_content,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return db_property


@router.put("/{property_id}/status", response_model=Property)
def change_property_status(
    property_id: int,
    status_in: PropertyStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    db_property = crud_property.get_property(db, property_id=property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if current_user.role == "tenant":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenants cannot change property status")
    if current_user.role == "landlord" and db_property.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if db_property.review_status != "approved" and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change property status before approval")
    if status_in.status not in {"vacant", "rented", "maintenance"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid property status")
    db_property.status = status_in.status
    db.commit()
    db.refresh(db_property)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_property_status",
        target_type="property",
        target_id=db_property.id,
        detail=f"Property status changed to {status_in.status}",
        ip_address=ip_address,
    )
    return db_property


@router.delete("/{property_id}", response_model=Property)
def delete_property(property_id: int, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_landlord)):
    db_property = crud_property.get_property(db, property_id=property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if db_property.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    removed = crud_property.remove_property(db, db_property)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="delete_property",
        target_type="property",
        target_id=removed.id,
        detail="Property deleted",
        ip_address=ip_address,
    )
    return removed
