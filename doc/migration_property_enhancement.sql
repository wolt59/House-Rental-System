-- 房源管理优化 - 数据库迁移脚本
-- 执行时间：2026-05-26
-- 说明：添加新的审核状态和发布状态支持

-- 1. 修改 review_status 字段的默认值和注释
ALTER TABLE properties 
MODIFY COLUMN review_status VARCHAR(30) DEFAULT 'draft' COMMENT '草稿/draft, 待审核/pending, 审核中/reviewing, 已通过/approved, 已拒绝/rejected';

-- 2. 修改 status 字段的默认值和注释
ALTER TABLE properties 
MODIFY COLUMN status VARCHAR(50) DEFAULT 'unpublished' COMMENT '已发布/published, 未发布/unpublished, 空置/vacant, 已出租/rented, 维修中/maintenance';

-- 3. 添加新的时间戳字段
ALTER TABLE properties 
ADD COLUMN submitted_at DATETIME NULL COMMENT '提交审核时间' AFTER review_comment,
ADD COLUMN approved_at DATETIME NULL COMMENT '审核通过时间' AFTER submitted_at,
ADD COLUMN published_at DATETIME NULL COMMENT '发布时间' AFTER approved_at,
ADD COLUMN unpublished_at DATETIME NULL COMMENT '暂停发布时间' AFTER published_at;

-- 4. 更新现有数据的状态（可选，根据实际需求调整）
-- 将现有的 pending 状态转为 draft（如果需要重新提交审核）
-- UPDATE properties SET review_status = 'draft' WHERE review_status = 'pending';

-- 将现有的 vacant 状态转为 unpublished（已审核通过但未发布的房源）
-- UPDATE properties SET status = 'unpublished' WHERE status = 'vacant' AND review_status = 'approved';

-- 5. 添加索引优化查询性能（如果索引已存在，请注释掉以下语句）
-- ALTER TABLE properties 
-- ADD INDEX idx_review_status (review_status),
-- ADD INDEX idx_status (status),
-- ADD INDEX idx_submitted_at (submitted_at),
-- ADD INDEX idx_published_at (published_at);

-- 完成提示
SELECT 'Migration completed successfully!' AS status;
