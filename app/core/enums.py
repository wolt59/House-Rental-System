from enum import Enum


class PropertyReviewStatus(str, Enum):
    """房源审核状态枚举"""
    DRAFT = "draft"  # 草稿（未提交审核）
    PENDING = "pending"  # 待审核（已提交，等待管理员处理）
    REVIEWING = "reviewing"  # 审核中（管理员正在审核）
    APPROVED = "approved"  # 已通过
    REJECTED = "rejected"  # 已拒绝


class PropertyStatus(str, Enum):
    """房源状态枚举"""
    PUBLISHED = "published"  # 已发布（租客可见）
    UNPUBLISHED = "unpublished"  # 未发布（租客不可见）
    VACANT = "vacant"  # 空置（已发布且未出租）
    RENTED = "rented"  # 已出租
    MAINTENANCE = "maintenance"  # 维修中


class PaymentStatus(str, Enum):
    """支付状态枚举"""
    PENDING = "pending"  # 待支付
    PAID = "paid"  # 已支付
    OVERDUE = "overdue"  # 逾期
    CANCELLED = "cancelled"  # 已取消


class BookingStatus(str, Enum):
    """预约状态枚举"""
    PENDING = "pending"  # 待确认
    APPROVED = "approved"  # 已同意
    REJECTED = "rejected"  # 已拒绝
    CANCELLED = "cancelled"  # 已取消
    NEGOTIATING = "negotiating"  # 待协商（房东提出改期）
    COMPLETED = "completed"  # 看房完成


class MaintenanceStatus(str, Enum):
    """维修请求状态枚举"""
    NEW = "new"  # 新建
    IN_PROGRESS = "in_progress"  # 处理中
    RESOLVED = "resolved"  # 已解决
    CLOSED = "closed"  # 已关闭


class ComplaintStatus(str, Enum):
    """投诉状态枚举"""
    OPEN = "open"  # 开放
    IN_PROGRESS = "in_progress"  # 处理中
    RESOLVED = "resolved"  # 已解决
    CLOSED = "closed"  # 已关闭


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"  # 管理员
    LANDLORD = "landlord"  # 房东
    TENANT = "tenant"  # 租客


class ContractStatus(str, Enum):
    """合同状态枚举"""
    DRAFT = "draft"  # 草稿
    PENDING_SIGN = "pending_sign"  # 待签约（双方都未签）
    PENDING_LANDLORD_SIGN = "pending_landlord_sign"  # 待房东签约
    PENDING_TENANT_SIGN = "pending_tenant_sign"  # 待租客签约
    ACTIVE = "active"  # 生效中
    TERMINATED = "terminated"  # 已终止
    CANCELLED = "cancelled"  # 已取消
    REJECTED = "rejected"  # 已拒绝
    EXPIRED = "expired"  # 已过期


# 可取消的合同状态（未签署或仅一方签署）
CANCELLABLE_STATUSES = [
    ContractStatus.DRAFT,
    ContractStatus.PENDING_SIGN,
    ContractStatus.PENDING_LANDLORD_SIGN,
    ContractStatus.PENDING_TENANT_SIGN,
]

# 可拒绝的合同状态
REJECTABLE_STATUSES = [
    ContractStatus.DRAFT,
    ContractStatus.PENDING_SIGN,
    ContractStatus.PENDING_LANDLORD_SIGN,
    ContractStatus.PENDING_TENANT_SIGN,
]

class MessageType(str, Enum):
    TEXT = "text"
    SYSTEM = "system"
    NOTIFICATION = "notification"


# 活跃/进行中的合同状态（占用房源）
ACTIVE_OR_PENDING_STATUSES = [
    ContractStatus.DRAFT,
    ContractStatus.PENDING_SIGN,
    ContractStatus.PENDING_LANDLORD_SIGN,
    ContractStatus.PENDING_TENANT_SIGN,
    ContractStatus.ACTIVE,
]
