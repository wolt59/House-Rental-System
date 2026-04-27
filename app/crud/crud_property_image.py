from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.property_image import PropertyImage
from app.schemas.property_image import PropertyImageCreate, PropertyImageUpdate


def get_property_image(db: Session, image_id: int) -> Optional[PropertyImage]:
    return db.query(PropertyImage).filter(PropertyImage.id == image_id).first()


def get_property_images(db: Session, property_id: int) -> List[PropertyImage]:
    return db.query(PropertyImage).filter(PropertyImage.property_id == property_id).order_by(PropertyImage.sort_order).all()


def create_property_image(db: Session, property_id: int, image_in: PropertyImageCreate) -> PropertyImage:
    image = PropertyImage(
        property_id=property_id,
        image_url=image_in.image_url,
        is_cover=image_in.is_cover or 0,
        sort_order=image_in.sort_order or 0,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def update_property_image(db: Session, db_image: PropertyImage, image_in: PropertyImageUpdate) -> PropertyImage:
    for field, value in image_in.dict(exclude_unset=True).items():
        setattr(db_image, field, value)
    db.commit()
    db.refresh(db_image)
    return db_image


def delete_property_image(db: Session, db_image: PropertyImage) -> PropertyImage:
    db.delete(db_image)
    db.commit()
    return db_image
