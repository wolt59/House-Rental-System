from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    user_id: int,
    action: str,
    target_type: str,
    target_id: Optional[int] = None,
    detail: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    audit = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit


def get_audit_logs(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    action_contains: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    detail_contains: Optional[str] = None,
    ip_address: Optional[str] = None,
    created_from: Optional[datetime] = None,
    created_to: Optional[datetime] = None,
) -> List[AuditLog]:
    query = db.query(AuditLog)
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if action is not None:
        query = query.filter(AuditLog.action == action)
    if action_contains is not None:
        query = query.filter(AuditLog.action.contains(action_contains))
    if target_type is not None:
        query = query.filter(AuditLog.target_type == target_type)
    if target_id is not None:
        query = query.filter(AuditLog.target_id == target_id)
    if detail_contains is not None:
        query = query.filter(AuditLog.detail.contains(detail_contains))
    if ip_address is not None:
        query = query.filter(AuditLog.ip_address.contains(ip_address))
    if created_from is not None:
        query = query.filter(AuditLog.created_at >= created_from)
    if created_to is not None:
        query = query.filter(AuditLog.created_at <= created_to)
    return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
