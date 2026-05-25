from enum import Enum


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

# 活跃/进行中的合同状态（占用房源）
ACTIVE_OR_PENDING_STATUSES = [
    ContractStatus.DRAFT,
    ContractStatus.PENDING_SIGN,
    ContractStatus.PENDING_LANDLORD_SIGN,
    ContractStatus.PENDING_TENANT_SIGN,
    ContractStatus.ACTIVE,
]
