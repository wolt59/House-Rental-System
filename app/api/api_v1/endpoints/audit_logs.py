from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_admin, get_db
from app.crud import crud_audit
from app.models.audit_log import AuditLog as AuditLogModel
from app.schemas.audit_log import AuditLog

router = APIRouter()


@router.get("/", response_model=List[AuditLog])
def list_audit_logs(
    skip: int = 0,
    limit: int = 20,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    action_contains: Optional[str] = None,
    detail_contains: Optional[str] = None,
    ip_address: Optional[str] = None,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_admin),
):
    return crud_audit.get_audit_logs(
        db,
        skip=skip,
        limit=limit,
        user_id=user_id,
        action=action,
        action_contains=action_contains,
        target_type=target_type,
        target_id=target_id,
        detail_contains=detail_contains,
        ip_address=ip_address,
        created_from=created_from,
        created_to=created_to,
    )


@router.get("/{audit_id}", response_model=AuditLog)
def read_audit_log(audit_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_active_admin)):
    item = db.query(AuditLogModel).filter(AuditLogModel.id == audit_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found")
    return item
