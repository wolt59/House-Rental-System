-- 预约功能增强迁移脚本
-- 执行时间：2026-05-27

-- 1. 添加新字段到 bookings 表
ALTER TABLE bookings 
ADD COLUMN reject_reason VARCHAR(500) NULL COMMENT '拒绝原因',
ADD COLUMN reschedule_proposal TEXT NULL COMMENT '改期建议',
ADD COLUMN reschedule_response VARCHAR(50) NULL COMMENT '租客对改期的响应',
ADD COLUMN completed_at DATETIME NULL COMMENT '看房完成时间',
ADD COLUMN landlord_contact_shown INT DEFAULT 0 COMMENT '是否已查看房东联系方式';

-- 2. 添加索引优化查询性能
ALTER TABLE bookings 
ADD INDEX idx_tenant_status (tenant_id, status),
ADD INDEX idx_property_status (property_id, status),
ADD INDEX idx_status (status),
ADD INDEX idx_appointment_time (appointment_time);

-- 3. 可选：如果需要更新现有数据的状态（根据实际情况决定是否需要）
-- UPDATE bookings SET status = 'pending' WHERE status NOT IN ('pending', 'approved', 'rejected', 'cancelled');

-- 迁移完成提示
SELECT 'Booking enhancement migration completed successfully!' AS migration_status;
