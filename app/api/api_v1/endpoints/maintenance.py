from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_landlord, get_current_active_user, get_current_active_admin, get_db
from app.crud import crud_audit, crud_maintenance
from app.models.maintenance import MaintenanceRequest
from app.models.property import Property
from app.schemas.maintenance import Maintenance, MaintenanceCreate, MaintenanceUpdate

router = APIRouter()


def _authorize_maintenance(request: MaintenanceRequest, current_user):
    if current_user.role == "admin":
        return
    if current_user.role == "landlord":
        if request.property.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to manage this request")
        return
    if current_user.role == "tenant" and request.tenant_id == current_user.id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


@router.post("/", response_model=Maintenance, status_code=status.HTTP_201_CREATED)
def create_maintenance(request_in: MaintenanceCreate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    property_obj = db.query(Property).filter(Property.id == request_in.property_id).first()
    if not property_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    maintenance = crud_maintenance.create_maintenance(db, tenant_id=current_user.id, maintenance_in=request_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="create_maintenance",
        target_type="maintenance",
        target_id=maintenance.id,
        detail=f"Maintenance request created for property {maintenance.property_id}",
        ip_address=ip_address,
    )
    return maintenance


@router.get("/", response_model=List[Maintenance])
def list_maintenance(
    skip: int = 0,
    limit: int = 20,
    status: str = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    query = db.query(MaintenanceRequest)
    if current_user.role == "tenant":
        query = query.filter(MaintenanceRequest.tenant_id == current_user.id)
    elif current_user.role == "landlord":
        query = query.join(Property).filter(Property.owner_id == current_user.id)
    if status is not None:
        query = query.filter(MaintenanceRequest.status == status)
    return query.offset(skip).limit(limit).all()


@router.get("/{request_id}", response_model=Maintenance)
def read_maintenance(request_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    request_item = crud_maintenance.get_maintenance(db, request_id)
    if not request_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance request not found")
    _authorize_maintenance(request_item, current_user)
    return request_item


@router.put("/{request_id}", response_model=Maintenance)
def update_maintenance(request_id: int, request_in: MaintenanceUpdate, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_active_user)):
    request_item = crud_maintenance.get_maintenance(db, request_id)
    if not request_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance request not found")
    _authorize_maintenance(request_item, current_user)

    if current_user.role == "tenant":
        if request_item.status != "new":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only new maintenance requests can be updated by tenant")
        if request_in.status and request_in.status != "new":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant cannot change status")
        if request_in.assigned_to is not None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant cannot assign maintenance tasks")
    else:
        if request_in.status and request_in.status not in {"new", "in_progress", "resolved", "closed"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid maintenance status")

    updated = crud_maintenance.update_maintenance(db, request_item, request_in)
    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="update_maintenance",
        target_type="maintenance",
        target_id=updated.id,
        detail=f"Maintenance request updated, status={updated.status}",
        ip_address=ip_address,
    )
    return updated
