from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, constr, field_validator

from app.schemas.common import UTCDatetimeModel


class PropertyImageBase(BaseModel):
    image_url: str
    image_type: Optional[str] = "photo"
    is_cover: Optional[int] = 0
    sort_order: Optional[int] = 0


class PropertyImage(PropertyImageBase, UTCDatetimeModel):
    id: int
    property_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PropertyBase(BaseModel):
    # 第一类：必填信息（业务核心数据）
    # 1. 位置地址类
    title: constr(min_length=3, max_length=200)
    city: Optional[str] = None  # 所属城市
    region: Optional[str] = None  # 行政区/区县
    address: constr(min_length=3, max_length=300)  # 详细门牌号
    community_name: Optional[str] = None  # 小区名称
    
    # 2. 房屋物理属性类
    property_type: Optional[str] = None  # 房源类型（整租/合租/公寓/商铺）
    rental_type: Optional[str] = None  # 房源类型别名
    floor_plan: Optional[str] = None  # 户型描述
    bedrooms: Optional[int] = None  # 卧室数量
    livingrooms: Optional[int] = None  # 客厅数量
    bathrooms: Optional[int] = None  # 卫生间数量
    area: Optional[float] = None  # 面积（兼容旧字段）
    building_area: Optional[float] = None  # 建筑面积
    usable_area: Optional[float] = None  # 实用面积
    decoration: Optional[str] = None  # 装修程度
    orientation: Optional[str] = None  # 房屋朝向
    floor_number: Optional[str] = None  # 所在楼层
    total_floors: Optional[int] = None  # 总楼层
    
    # 3. 租赁价格与押金类
    rent: float  # 每月租金
    deposit: Optional[float] = None  # 押金金额
    payment_method: Optional[str] = None  # 付款方式
    
    # 4. 租期与入住规则类
    min_lease_term: Optional[int] = None  # 最短租期（月）
    earliest_move_in_date: Optional[str] = None  # 最早可入住时间
    
    # 5. 费用权责划分
    property_fee_bearer: Optional[str] = None  # 物业费承担方
    utility_fee_bearer: Optional[str] = None  # 水电燃气费承担方
    other_fee_bearer: Optional[str] = None  # 其他费用承担方
    
    # 6. 房屋使用限制
    allow_pets: Optional[int] = 0  # 是否允许宠物
    
    # 7. 基础展示项
    description: Optional[str] = None  # 房源简介/详细描述
    
    # 第二类：选填信息（丰富房源介绍）
    # 1. 房屋补充属性
    build_year: Optional[int] = None  # 建筑年代
    has_elevator: Optional[int] = None  # 电梯配置
    total_households: Optional[int] = None  # 总户数
    property_management_type: Optional[str] = None  # 物业类型
    
    # 2. 室内配套设施
    facilities: Optional[str] = None  # 设施清单
    
    # 3. 周边配套描述
    surrounding: Optional[str] = None  # 周边环境
    
    # 4. 看房时间规则
    viewing_time_rules: Optional[str] = None  # 看房时间段
    
    # 5. 图文内容
    video_url: Optional[str] = None  # 视频链接
    latitude: Optional[float] = None  # 纬度
    longitude: Optional[float] = None  # 经度
    
    # 6. 特色标签
    tags: Optional[str] = None  # 特色标签
    
    # 7. 个人补充备注
    landlord_notes: Optional[str] = None  # 房东备注


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    # 第一类：必填信息
    title: Optional[constr(min_length=3, max_length=200)] = None
    city: Optional[str] = None
    region: Optional[str] = None
    address: Optional[constr(min_length=3, max_length=300)] = None
    community_name: Optional[str] = None
    
    property_type: Optional[str] = None
    rental_type: Optional[str] = None
    floor_plan: Optional[str] = None
    bedrooms: Optional[int] = None
    livingrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area: Optional[float] = None
    building_area: Optional[float] = None
    usable_area: Optional[float] = None
    decoration: Optional[str] = None
    orientation: Optional[str] = None
    floor_number: Optional[str] = None
    total_floors: Optional[int] = None
    
    rent: Optional[float] = None
    deposit: Optional[float] = None
    payment_method: Optional[str] = None
    
    min_lease_term: Optional[int] = None
    earliest_move_in_date: Optional[str] = None
    
    property_fee_bearer: Optional[str] = None
    utility_fee_bearer: Optional[str] = None
    other_fee_bearer: Optional[str] = None
    
    allow_pets: Optional[int] = None
    description: Optional[str] = None
    
    # 第二类：选填信息
    build_year: Optional[int] = None
    has_elevator: Optional[int] = None
    total_households: Optional[int] = None
    property_management_type: Optional[str] = None
    facilities: Optional[str] = None
    surrounding: Optional[str] = None
    viewing_time_rules: Optional[str] = None
    video_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    tags: Optional[str] = None
    landlord_notes: Optional[str] = None
    
    status: Optional[str] = None
    review_status: Optional[str] = None


class PropertyInDBBase(PropertyBase, UTCDatetimeModel):
    id: int
    owner_id: int
    view_count: int
    status: str
    review_status: str
    review_comment: Optional[str] = None
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    unpublished_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    images: Optional[List[PropertyImage]] = []

    class Config:
        from_attributes = True
    
    @field_validator('earliest_move_in_date', mode='before')
    @classmethod
    def convert_date_to_string(cls, v):
        """将 date 类型转换为 string，确保 API 响应格式一致"""
        if isinstance(v, date):
            return v.isoformat()
        return v


class Property(PropertyInDBBase):
    pass


class PropertyReview(BaseModel):
    review_status: str
    comment: Optional[str] = None


class PropertyStatusUpdate(BaseModel):
    status: str


class PropertySubmitForReview(BaseModel):
    """提交审核请求"""
    pass


class PropertyRepublish(BaseModel):
    """重新发布请求"""
    pass


class RegionStats(BaseModel):
    region: str
    property_count: int

    class Config:
        from_attributes = True


class FloorPlanStats(BaseModel):
    floor_plan: str
    property_count: int

    class Config:
        from_attributes = True
