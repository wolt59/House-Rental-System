from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.maintenance import MaintenanceRequest
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate


def get_maintenance(db: Session, request_id: int) -> Optional[MaintenanceRequest]:
    return db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()


def get_maintenances(
    db: Session,
    tenant_id: Optional[int] = None,
    property_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> List[MaintenanceRequest]:
    query = db.query(MaintenanceRequest)
    if tenant_id is not None:
        query = query.filter(MaintenanceRequest.tenant_id == tenant_id)
    if property_id is not None:
        query = query.filter(MaintenanceRequest.property_id == property_id)
    if status is not None:
        query = query.filter(MaintenanceRequest.status == status)
    return query.offset(skip).limit(limit).all()


def create_maintenance(db: Session, tenant_id: int, maintenance_in: MaintenanceCreate) -> MaintenanceRequest:
    maintenance = MaintenanceRequest(
        property_id=maintenance_in.property_id,
        tenant_id=tenant_id,
        title=maintenance_in.title,
        description=maintenance_in.description,
        image_urls=maintenance_in.image_urls,
        priority=maintenance_in.priority or "normal",
    )
    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)
    return maintenance


def update_maintenance(db: Session, db_maintenance: MaintenanceRequest, maintenance_in: MaintenanceUpdate) -> MaintenanceRequest:
    for field, value in maintenance_in.dict(exclude_unset=True).items():
        setattr(db_maintenance, field, value)
    db.commit()
    db.refresh(db_maintenance)
    return db_maintenance
