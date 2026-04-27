from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.schemas.complaint import ComplaintCreate, ComplaintUpdate


def get_complaint(db: Session, complaint_id: int) -> Optional[Complaint]:
    return db.query(Complaint).filter(Complaint.id == complaint_id).first()


def get_complaints(
    db: Session,
    tenant_id: Optional[int] = None,
    property_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[Complaint]:
    query = db.query(Complaint)
    if tenant_id is not None:
        query = query.filter(Complaint.tenant_id == tenant_id)
    if property_id is not None:
        query = query.filter(Complaint.property_id == property_id)
    if status is not None:
        query = query.filter(Complaint.status == status)
    return query.offset(skip).limit(limit).all()


def create_complaint(db: Session, tenant_id: int, complaint_in: ComplaintCreate) -> Complaint:
    complaint = Complaint(
        property_id=complaint_in.property_id,
        tenant_id=tenant_id,
        complaint_type=complaint_in.complaint_type,
        title=complaint_in.title,
        content=complaint_in.content,
        image_urls=complaint_in.image_urls,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


def update_complaint(db: Session, db_complaint: Complaint, complaint_in: ComplaintUpdate) -> Complaint:
    for field, value in complaint_in.dict(exclude_unset=True).items():
        setattr(db_complaint, field, value)
    db.commit()
    db.refresh(db_complaint)
    return db_complaint
