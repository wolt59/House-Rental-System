-- 房源表单增强 - 数据库迁移脚本
-- 执行时间：2026-05-28
-- 说明：根据新的房源发布需求，添加必填和选填字段

-- ==================== 第一类：必填信息（业务核心数据）====================

-- 1. 位置地址类
ALTER TABLE properties 
ADD COLUMN city VARCHAR(50) NULL COMMENT '所属城市' AFTER region,
ADD COLUMN community_name VARCHAR(200) NULL COMMENT '小区名称' AFTER address;

-- 2. 房屋物理属性类
ALTER TABLE properties 
ADD COLUMN rental_type VARCHAR(50) NULL COMMENT '房源类型（整租/合租/公寓/商铺）' AFTER property_type,
ADD COLUMN bedrooms INT NULL COMMENT '卧室数量' AFTER floor_plan,
ADD COLUMN livingrooms INT NULL COMMENT '客厅数量' AFTER bedrooms,
ADD COLUMN bathrooms INT NULL COMMENT '卫生间数量' AFTER livingrooms,
ADD COLUMN building_area FLOAT NULL COMMENT '建筑面积（㎡）' AFTER area,
ADD COLUMN usable_area FLOAT NULL COMMENT '实用面积（㎡）' AFTER building_area;

-- 3. 租赁价格与押金类
ALTER TABLE properties 
ADD COLUMN payment_method VARCHAR(50) NULL COMMENT '付款方式（押一付一/押一付三/半年付/年付）' AFTER deposit;

-- 4. 租期与入住规则类
ALTER TABLE properties 
ADD COLUMN min_lease_term INT NULL COMMENT '最短租期（月）' AFTER payment_method,
ADD COLUMN earliest_move_in_date DATE NULL COMMENT '最早可入住时间' AFTER min_lease_term;

-- 5. 费用权责划分
ALTER TABLE properties 
ADD COLUMN property_fee_bearer VARCHAR(50) NULL COMMENT '物业费承担方（房东/租客）' AFTER earliest_move_in_date,
ADD COLUMN utility_fee_bearer VARCHAR(100) NULL COMMENT '水电燃气费承担方' AFTER property_fee_bearer,
ADD COLUMN other_fee_bearer VARCHAR(200) NULL COMMENT '网络、垃圾清运等其他费用承担方' AFTER utility_fee_bearer;

-- 6. 房屋使用限制
ALTER TABLE properties 
ADD COLUMN allow_pets TINYINT(1) DEFAULT 0 COMMENT '是否允许饲养宠物（0=否，1=是）' AFTER other_fee_bearer;

-- ==================== 第二类：选填信息（丰富房源介绍）====================

-- 1. 房屋补充属性
ALTER TABLE properties 
ADD COLUMN build_year INT NULL COMMENT '建筑建成年代' AFTER usable_area,
ADD COLUMN has_elevator TINYINT(1) DEFAULT NULL COMMENT '电梯配置（0=无，1=有）' AFTER build_year,
ADD COLUMN total_households INT NULL COMMENT '总户数' AFTER has_elevator,
ADD COLUMN property_management_type VARCHAR(100) NULL COMMENT '物业类型' AFTER total_households;

-- 2. 室内配套设施（已存在facilities字段，保持不变）

-- 3. 周边配套描述（已存在surrounding字段，保持不变）

-- 4. 看房时间规则
ALTER TABLE properties 
ADD COLUMN viewing_time_rules VARCHAR(500) NULL COMMENT '日常可接待看房的时间段' AFTER surrounding;

-- 5. 图文与描述内容（已存在description字段，保持不变）

-- 6. 特色标签
ALTER TABLE properties 
ADD COLUMN tags VARCHAR(500) NULL COMMENT '特色标签（近地铁/拎包入住/采光好等，逗号分隔）' AFTER description;

-- 7. 个人补充备注
ALTER TABLE properties 
ADD COLUMN landlord_notes TEXT NULL COMMENT '房东额外说明、特殊要求等' AFTER tags;

-- 完成提示
SELECT '房源表单增强迁移完成！' AS status;
