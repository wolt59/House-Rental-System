from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_active_landlord, get_current_active_admin, get_db
from app.crud import crud_audit, crud_property, crud_property_image
from app.schemas.property_image import PropertyImage, PropertyImageCreate, PropertyImageUpdate

router = APIRouter()


@router.post("/{property_id}/images", response_model=PropertyImage, status_code=status.HTTP_201_CREATED)
def add_property_image(
    property_id: int,
    image_in: PropertyImageCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_landlord),
):
    db_property = crud_property.get_property(db, property_id)
    if not db_property:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if db_property.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    image = crud_property_image.create_property_image(db, property_id=property_id, image_in=image_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="add_property_image",
        target_type="property_image",
        target_id=image.id,
        detail=f"Image added to property {property_id}",
        ip_address=ip_address,
    )
    return image


@router.get("/{property_id}/images", response_model=List[PropertyImage])
def list_property_images(
    property_id: int,
    db: Session = Depends(get_db),
):
    return crud_property_image.get_property_images(db, property_id=property_id)


@router.put("/images/{image_id}", response_model=PropertyImage)
def update_property_image(
    image_id: int,
    image_in: PropertyImageUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_landlord),
):
    image = crud_property_image.get_property_image(db, image_id)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    db_property = crud_property.get_property(db, image.property_id)
    if db_property.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    updated = crud_property_image.update_property_image(db, image, image_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_property_image",
        target_type="property_image",
        target_id=updated.id,
        detail="Property image updated",
        ip_address=ip_address,
    )
    return updated


@router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property_image(
    image_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_landlord),
):
    image = crud_property_image.get_property_image(db, image_id)
    if not image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    db_property = crud_property.get_property(db, image.property_id)
    if db_property.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    crud_property_image.delete_property_image(db, image)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="delete_property_image",
        target_type="property_image",
        target_id=image_id,
        detail="Property image deleted",
        ip_address=ip_address,
    )
    return None
