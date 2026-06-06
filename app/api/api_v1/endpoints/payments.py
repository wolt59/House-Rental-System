from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_current_active_admin, get_db
from app.api.websocket import ws_manager
from app.crud import crud_audit, crud_payment, crud_contract, crud_message
from app.models.message import Message
from app.models.property import Property
from app.schemas.payment import (
    Payment as PaymentSchema,
    PaymentWithDetails,
    PaymentCreate,
    PaymentSubmit,
    PaymentUpdate,
    PaymentReject,
)
from app.core.enums import PaymentStatus, MessageType

router = APIRouter()


def _enrich_payment(db: Session, payment) -> dict:
    """为账单附加租客名、房东名、房源标题、合同编号"""
    data = {
        "id": payment.id,
        "bill_no": payment.bill_no,
        "payment_no": payment.payment_no,
        "contract_id": payment.contract_id,
        "property_id": payment.property_id,
        "landlord_id": payment.landlord_id,
        "tenant_id": payment.tenant_id,
        "bill_type": payment.bill_type,
        "period": payment.period,
        "due_amount": payment.due_amount,
        "actual_amount": payment.actual_amount,
        "payment_method": payment.payment_method,
        "payment_time": payment.payment_time,
        "payment_proof": payment.payment_proof,
        "transaction_note": payment.transaction_note,
        "status": payment.status,
        "due_date": payment.due_date,
        "paid_at": payment.paid_at,
        "confirmed_at": payment.confirmed_at,
        "overdue_days": payment.overdue_days,
        "overdue_fee": payment.overdue_fee,
        "rejected_reason": payment.rejected_reason,
        "remark": payment.remark,
        "created_at": payment.created_at,
        "updated_at": payment.updated_at,
        "tenant_name": None,
        "landlord_name": None,
        "property_title": None,
        "contract_no": None,
    }
    try:
        if payment.tenant:
            data["tenant_name"] = payment.tenant.full_name or payment.tenant.username
    except Exception:
        pass
    try:
        if payment.landlord:
            data["landlord_name"] = payment.landlord.full_name or payment.landlord.username
    except Exception:
        pass
    try:
        if payment.property:
            data["property_title"] = payment.property.title
    except Exception:
        pass
    try:
        if payment.contract:
            data["contract_no"] = payment.contract.contract_no
    except Exception:
        pass
    return data


@router.post("/", response_model=PaymentSchema, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment_in: PaymentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """创建账单（管理员或系统使用）"""
    contract = crud_contract.get_contract(db, payment_in.contract_id)
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")

    # 权限检查
    if current_user.role != "admin" and contract.landlord_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权创建账单")

    payment = crud_payment.create_payment(db, tenant_id=contract.tenant_id, payment_in=payment_in)

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db,
        user_id=current_user.id,
        action="create_payment",
        target_type="payment",
        target_id=payment.id,
        detail=f"账单创建: {payment.bill_no}, 类型={payment.bill_type}, 金额={payment.due_amount}",
        ip_address=ip_address,
    )
    return payment


@router.get("/", response_model=List[dict])
def list_payments(
    contract_id: Optional[int] = Query(None),
    property_id: Optional[int] = Query(None),
    property_title: Optional[str] = Query(None, description="按房源标题模糊搜索"),
    status: Optional[str] = Query(None),
    bill_type: Optional[str] = Query(None),
    due_date_from: Optional[datetime] = Query(None, description="截止日期起始（含）"),
    due_date_to: Optional[datetime] = Query(None, description="截止日期结束（含）"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """获取账单列表（根据角色过滤，支持日期范围和房源筛选）"""
    base_kwargs = dict(
        contract_id=contract_id, property_id=property_id,
        property_title=property_title,
        status=status, bill_type=bill_type,
        due_date_from=due_date_from, due_date_to=due_date_to,
        skip=skip, limit=limit,
    )
    if current_user.role == "admin":
        payments = crud_payment.get_payments(db, **base_kwargs)
    elif current_user.role == "landlord":
        payments = crud_payment.get_payments(db, landlord_id=current_user.id, **base_kwargs)
    else:
        payments = crud_payment.get_payments(db, tenant_id=current_user.id, **base_kwargs)

    return [_enrich_payment(db, p) for p in payments]


@router.get("/stats")
def payment_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """获取收款统计"""
    if current_user.role == "admin":
        total_due = sum(
            p.due_amount for p in crud_payment.get_payments(db, status=PaymentStatus.CONFIRMED, limit=10000)
        )
        total_pending = sum(
            p.due_amount for p in crud_payment.get_payments(db, status=PaymentStatus.PENDING, limit=10000)
        )
        total_overdue = sum(
            p.due_amount for p in crud_payment.get_payments(db, status=PaymentStatus.OVERDUE, limit=10000)
        )
    elif current_user.role == "landlord":
        total_due = sum(
            p.due_amount for p in crud_payment.get_payments(
                db, landlord_id=current_user.id, status=PaymentStatus.CONFIRMED, limit=10000
            )
        )
        total_pending = sum(
            p.due_amount for p in crud_payment.get_payments(
                db, landlord_id=current_user.id, status=PaymentStatus.PENDING, limit=10000
            )
        )
        total_overdue = sum(
            p.due_amount for p in crud_payment.get_payments(
                db, landlord_id=current_user.id, status=PaymentStatus.OVERDUE, limit=10000
            )
        )
    else:
        total_due = sum(
            p.due_amount for p in crud_payment.get_payments(
                db, tenant_id=current_user.id, status=PaymentStatus.CONFIRMED, limit=10000
            )
        )
        total_pending = sum(
            p.due_amount for p in crud_payment.get_payments(
                db, tenant_id=current_user.id, status=PaymentStatus.PENDING, limit=10000
            )
        )
        total_overdue = sum(
            p.due_amount for p in crud_payment.get_payments(
                db, tenant_id=current_user.id, status=PaymentStatus.OVERDUE, limit=10000
            )
        )

    return {
        "total_confirmed": round(total_due, 2),
        "total_pending": round(total_pending, 2),
        "total_overdue": round(total_overdue, 2),
    }


@router.get("/{payment_id}")
def read_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """获取账单详情"""
    payment = crud_payment.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账单不存在")

    contract = crud_contract.get_contract(db, payment.contract_id)
    if current_user.role != "admin" and payment.tenant_id != current_user.id and \
            (not contract or contract.landlord_id != current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看此账单")

    return _enrich_payment(db, payment)


@router.put("/{payment_id}/submit")
def submit_payment(
    payment_id: int,
    submit_in: PaymentSubmit,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """租客提交付款凭证"""
    payment = crud_payment.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账单不存在")
    if payment.tenant_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此账单")
    if payment.status not in [PaymentStatus.PENDING, PaymentStatus.OVERDUE, PaymentStatus.REJECTED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"当前状态({payment.status})不允许提交付款")

    updated = crud_payment.submit_payment(db, payment, submit_in)

    # 通知房东
    from app.models.message import Message
    msg = Message(
        from_user_id=current_user.id,
        to_user_id=payment.landlord_id,
        content=f"租客已提交账单（编号：{payment.bill_no}）的付款凭证，请登录系统确认收款。",
        property_id=payment.property_id,
        is_read=False,
        message_type="notification",
    )
    db.add(msg)
    db.commit()

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db, user_id=current_user.id, action="submit_payment",
        target_type="payment", target_id=updated.id,
        detail=f"账单 {updated.bill_no} 提交付款, 金额={updated.actual_amount}",
        ip_address=ip_address,
    )
    return _enrich_payment(db, updated)


@router.put("/{payment_id}/confirm")
def confirm_payment(
    payment_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """房东确认收款"""
    payment = crud_payment.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账单不存在")
    if payment.landlord_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此账单")
    if payment.status != PaymentStatus.SUBMITTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只有已提交付款的账单才能确认收款")

    updated = crud_payment.confirm_payment(db, payment)

    # 通知租客
    from app.models.message import Message
    msg = Message(
        from_user_id=current_user.id,
        to_user_id=payment.tenant_id,
        content=f"房东已确认收到账单（编号：{payment.bill_no}）的付款。",
        property_id=payment.property_id,
        is_read=False,
        message_type="notification",
    )
    db.add(msg)
    db.commit()

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db, user_id=current_user.id, action="confirm_payment",
        target_type="payment", target_id=updated.id,
        detail=f"账单 {updated.bill_no} 确认收款",
        ip_address=ip_address,
    )
    return _enrich_payment(db, updated)


@router.put("/{payment_id}/reject")
def reject_payment(
    payment_id: int,
    reject_in: PaymentReject,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """房东驳回付款"""
    payment = crud_payment.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账单不存在")
    if payment.landlord_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此账单")
    if payment.status != PaymentStatus.SUBMITTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="只有已提交付款的账单才能驳回")

    updated = crud_payment.reject_payment(db, payment, reject_in.rejected_reason)

    # 通知租客
    from app.models.message import Message
    msg = Message(
        from_user_id=current_user.id,
        to_user_id=payment.tenant_id,
        content=f"房东驳回了账单（编号：{payment.bill_no}）的付款。原因：{reject_in.rejected_reason}",
        property_id=payment.property_id,
        is_read=False,
        message_type="notification",
    )
    db.add(msg)
    db.commit()

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db, user_id=current_user.id, action="reject_payment",
        target_type="payment", target_id=updated.id,
        detail=f"账单 {updated.bill_no} 驳回付款, 原因={reject_in.rejected_reason}",
        ip_address=ip_address,
    )
    return _enrich_payment(db, updated)


@router.post("/{payment_id}/remind")
def remind_payment(
    payment_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """房东提醒租客付款（发送通知消息）"""
    payment = crud_payment.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账单不存在")
    if payment.landlord_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作")

    property_title = ""
    if payment.property_id:
        prop = db.query(Property).filter(Property.id == payment.property_id).first()
        property_title = prop.title if prop else ""

    content = (
        f"房东提醒您：请尽快支付账单「{payment.bill_no}」"
        f"（{property_title}，金额 ¥{payment.due_amount}）。"
        f"截止日期：{payment.due_date.strftime('%Y-%m-%d') if payment.due_date else '-'}。"
    )

    msg = Message(
        from_user_id=current_user.id,
        to_user_id=payment.tenant_id,
        property_id=payment.property_id,
        content=content,
        message_type=MessageType.NOTIFICATION.value,
    )
    db.add(msg)
    db.flush()
    db.refresh(msg)

    unread_before = crud_message.get_unread_count(db, user_id=payment.tenant_id, message_type="notification")

    async def notify_tenant():
        payload = {
            "type": "new_message",
            "message": {
                "id": msg.id,
                "from_user_id": msg.from_user_id,
                "to_user_id": msg.to_user_id,
                "content": msg.content,
                "message_type": msg.message_type,
                "property_id": msg.property_id,
                "is_read": msg.is_read,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            },
            "unread_count": unread_before + 1,
        }
        await ws_manager.send_personal(payload, msg.to_user_id)

    background_tasks.add_task(notify_tenant)
    db.commit()

    return {"message": "提醒已发送", "payment_id": payment_id}


@router.put("/{payment_id}")
def update_payment(
    payment_id: int,
    payment_in: PaymentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_admin),
):
    """管理员更新账单"""
    payment = crud_payment.get_payment(db, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="账单不存在")

    updated = crud_payment.update_payment(db, payment, payment_in)

    ip_address = request.client.host if request.client else None
    crud_audit.create_audit_log(
        db, user_id=current_user.id, action="update_payment",
        target_type="payment", target_id=updated.id,
        detail=f"账单 {updated.bill_no} 已更新, 状态={updated.status}",
        ip_address=ip_address,
    )
    return _enrich_payment(db, updated)


@router.post("/admin/generate-overdue")
def trigger_overdue_check(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_admin),
):
    """管理员手动触发逾期检查"""
    count = crud_payment.check_and_mark_overdue(db)
    return {"message": f"逾期检查完成", "overdue_count": count}


@router.post("/admin/generate-next-month")
def trigger_next_month_bills(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_admin),
):
    """管理员手动触发生成下月账单"""
    bills = crud_payment.generate_next_month_bills(db)
    return {"message": f"下月账单生成完成", "count": len(bills)}
