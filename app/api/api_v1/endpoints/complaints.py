from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_landlord, get_current_active_user, get_current_active_admin, get_db
from app.crud import crud_audit, crud_complaint
from app.models.complaint import Complaint
from app.models.property import Property
from app.schemas.complaint import Complaint as ComplaintSchema, ComplaintCreate, ComplaintUpdate

router = APIRouter()


def _authorize_complaint(complaint: Complaint, current_user):
    if current_user.role == "admin":
        return
    if current_user.role == "landlord":
        if complaint.property.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to manage this complaint")
        return
    if current_user.role == "tenant" and complaint.tenant_id == current_user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


@router.post("/", response_model=ComplaintSchema, status_code=status.HTTP_201_CREATED)
def create_complaint(complaint_in: ComplaintCreate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    property_obj = db.query(Property).filter(Property.id == complaint_in.property_id).first()
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    complaint = crud_complaint.create_complaint(db, tenant_id=current_user.id, complaint_in=complaint_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="create_complaint",
        target_type="complaint",
        target_id=complaint.id,
        detail=f"Complaint created for property {complaint.property_id}",
        ip_address=ip_address,
    )
    return complaint


@router.get("/", response_model=List[ComplaintSchema])
def list_complaints(
    skip: int = 0,
    limit: int = 20,
    status: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    query = db.query(Complaint)
    if current_user.role == "tenant":
        query = query.filter(Complaint.tenant_id == current_user.id)
    elif current_user.role == "landlord":
        query = query.join(Property).filter(Property.owner_id == current_user.id)
    if status is not None:
        query = query.filter(Complaint.status == status)
    return query.offset(skip).limit(limit).all()


@router.get("/{complaint_id}", response_model=ComplaintSchema)
def read_complaint(complaint_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    complaint = crud_complaint.get_complaint(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    _authorize_complaint(complaint, current_user)
    return complaint


@router.put("/{complaint_id}", response_model=ComplaintSchema)
def update_complaint(complaint_id: int, complaint_in: ComplaintUpdate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    complaint = crud_complaint.get_complaint(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    _authorize_complaint(complaint, current_user)

    if current_user.role == "tenant":
        if complaint.status != "open":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only open complaints may be updated by tenant")
        if complaint_in.status and complaint_in.status != "open":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant cannot change complaint status")
        if complaint_in.handled_by is not None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant cannot assign handlers")
    else:
        if complaint_in.status and complaint_in.status not in {"open", "in_progress", "resolved", "closed"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid complaint status")

    updated = crud_complaint.update_complaint(db, complaint, complaint_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_complaint",
        target_type="complaint",
        target_id=updated.id,
        detail=f"Complaint updated, status={updated.status}",
        ip_address=ip_address,
    )
    return updated
