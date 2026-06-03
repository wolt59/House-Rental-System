-- =====================================================
-- 收款功能增强 - 数据库迁移脚本 (MySQL)
-- 将原有的简单 payments 表扩展为完整的账单系统
-- 注意：请在执行前备份数据库
-- =====================================================

START TRANSACTION;

-- 1. 重命名 amount 为 due_amount（兼容 MySQL 5.7+）
ALTER TABLE payments CHANGE COLUMN amount due_amount FLOAT NOT NULL COMMENT '应收金额';

-- 2. 新增账单编号字段
ALTER TABLE payments ADD COLUMN bill_no VARCHAR(50) NULL COMMENT '账单编号' AFTER id;
ALTER TABLE payments ADD UNIQUE INDEX ix_payments_bill_no (bill_no);

-- 3. 新增房源ID字段（冗余外键，便于查询）
ALTER TABLE payments ADD COLUMN property_id INT NULL COMMENT '房源ID' AFTER contract_id;
ALTER TABLE payments ADD CONSTRAINT fk_payments_property_id 
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE SET NULL;

-- 4. 新增房东ID字段（冗余外键，便于查询）
ALTER TABLE payments ADD COLUMN landlord_id INT NULL COMMENT '房东ID' AFTER property_id;
ALTER TABLE payments ADD CONSTRAINT fk_payments_landlord_id 
    FOREIGN KEY (landlord_id) REFERENCES users(id) ON DELETE SET NULL;

-- 5. 新增账单类型字段
ALTER TABLE payments ADD COLUMN bill_type VARCHAR(50) DEFAULT 'rent' COMMENT '账单类型' AFTER due_amount;

-- 6. 新增所属周期字段
ALTER TABLE payments ADD COLUMN period VARCHAR(20) NULL COMMENT '所属周期，如2026-01' AFTER bill_type;

-- 7. 新增实付金额字段
ALTER TABLE payments ADD COLUMN actual_amount FLOAT NULL COMMENT '实付金额' AFTER period;

-- 8. 新增付款时间字段
ALTER TABLE payments ADD COLUMN payment_time DATETIME NULL COMMENT '付款时间' AFTER payment_method;

-- 9. 新增付款凭证字段
ALTER TABLE payments ADD COLUMN payment_proof VARCHAR(500) NULL COMMENT '付款凭证URL' AFTER payment_time;

-- 10. 新增转账备注字段
ALTER TABLE payments ADD COLUMN transaction_note VARCHAR(500) NULL COMMENT '转账备注' AFTER payment_proof;

-- 11. 新增确认收款时间字段
ALTER TABLE payments ADD COLUMN confirmed_at DATETIME NULL COMMENT '确认收款时间' AFTER paid_at;

-- 12. 新增驳回原因字段
ALTER TABLE payments ADD COLUMN rejected_reason VARCHAR(500) NULL COMMENT '驳回原因' AFTER overdue_fee;

-- 13. 为现有数据生成账单编号（使用 MySQL 的 DATE_FORMAT + LPAD）
UPDATE payments 
SET bill_no = CONCAT('BILL', DATE_FORMAT(IFNULL(created_at, NOW()), '%Y%m%d%H%i%S'), LPAD(id, 5, '0'))
WHERE bill_no IS NULL;

-- 14. 从合同表回填 property_id 和 landlord_id
UPDATE payments p
INNER JOIN contracts c ON c.id = p.contract_id
SET p.property_id = c.property_id,
    p.landlord_id = c.landlord_id
WHERE p.property_id IS NULL OR p.landlord_id IS NULL;

-- 15. 为现有数据设置账单类型（默认为租金）
UPDATE payments SET bill_type = 'rent' WHERE bill_type IS NULL;

-- 16. 如果原有的 payment_no 为空，设置默认值
UPDATE payments 
SET payment_no = CONCAT('PAY', DATE_FORMAT(IFNULL(created_at, NOW()), '%Y%m%d%H%i%S'), LPAD(id, 5, '0'))
WHERE payment_no IS NULL AND status = 'paid';

-- 17. 为支付的账单设置 due_date（如果没有的话，取创建时间）
UPDATE payments 
SET due_date = created_at 
WHERE due_date IS NULL AND status IN ('pending', 'paid', 'overdue');

COMMIT;

-- =====================================================
-- 迁移完成
-- 如需回滚，请使用备份数据恢复
-- =====================================================
