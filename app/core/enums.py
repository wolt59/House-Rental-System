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
    UNPUBLISHED = "unpublished"  # 未发布（草稿或下架，租客不可见）
    PUBLISHED = "published"  # 已发布（空置状态，租客可见可租）
    RENTED = "rented"  # 已出租（有生效合同）


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


class ContractApplicationStatus(str, Enum):
    """合约申请状态枚举"""
    APPLY_PENDING = "apply_pending"  # 待房东确认
    APPLY_APPROVED = "apply_approved"  # 房东已同意，已生成合同草稿
    APPLY_REJECTED = "apply_rejected"  # 房东已拒绝
    APPLY_CANCELLED = "apply_cancelled"  # 租客已取消


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
    DRAFT = "draft"  # 草稿，可编辑
    PENDING_SIGN = "pending_sign"  # 待签署（双方都未签）
    PART_SIGNED = "part_signed"  # 一方已签署，内容已锁定
    ACTIVE = "active"  # 双方已签署，合同生效
    CHANGE_NEGOTIATING = "change_negotiating"  # 变更协商中
    TERMINATE_NEGOTIATING = "terminate_negotiating"  # 解约协商中
    TERMINATED = "terminated"  # 已提前解约
    EXPIRED = "expired"  # 已到期
    CANCELLED = "cancelled"  # 已取消


# 可取消的合同状态（草稿或待签署状态）
CANCELLABLE_STATUSES = [
    ContractStatus.DRAFT,
    ContractStatus.PENDING_SIGN,
]

class MessageType(str, Enum):
    TEXT = "text"
    SYSTEM = "system"
    NOTIFICATION = "notification"


# 活跃/进行中的合同状态（占用房源）
ACTIVE_OR_PENDING_STATUSES = [
    ContractStatus.DRAFT,
    ContractStatus.PENDING_SIGN,
    ContractStatus.PART_SIGNED,
    ContractStatus.ACTIVE,
]
