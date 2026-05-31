-- ============================================================
-- 电子合同系统增强迁移脚本
-- 执行时间: 2026-05-30
-- 说明: 添加合约申请、合同变更、提前解约功能
-- ============================================================

-- 1. 扩展 contracts 表字段
ALTER TABLE contracts 
ADD COLUMN payment_method VARCHAR(50) COMMENT '付款方式' AFTER deposit,
ADD COLUMN min_lease_term INT COMMENT '最短租期（月）' AFTER payment_day,
ADD COLUMN renewal_notice_days INT COMMENT '续租提醒天数' AFTER min_lease_term,
ADD COLUMN check_in_time DATETIME COMMENT '入住时间' AFTER renewal_notice_days,
ADD COLUMN allow_pets INT DEFAULT 0 COMMENT '是否允许养宠物（0=否，1=是）' AFTER check_in_time,
ADD COLUMN early_termination_days INT COMMENT '解约提前天数' AFTER allow_pets,
ADD COLUMN property_fee_bearer VARCHAR(50) COMMENT '物业费承担方' AFTER early_termination_days,
ADD COLUMN utility_fee_bearer VARCHAR(100) COMMENT '水电燃气承担方' AFTER property_fee_bearer,
ADD COLUMN other_fee_bearer VARCHAR(200) COMMENT '其他费用承担方' AFTER utility_fee_bearer,
ADD COLUMN additional_terms TEXT COMMENT '补充约定' AFTER other_fee_bearer,
ADD COLUMN landlord_sign_ip VARCHAR(45) COMMENT '房东签署IP' AFTER tenant_signed_at,
ADD COLUMN landlord_sign_device VARCHAR(200) COMMENT '房东签署设备信息' AFTER landlord_sign_ip,
ADD COLUMN tenant_sign_ip VARCHAR(45) COMMENT '租客签署IP' AFTER landlord_sign_device,
ADD COLUMN tenant_sign_device VARCHAR(200) COMMENT '租客签署设备信息' AFTER tenant_sign_ip,
ADD COLUMN landlord_signature_image VARCHAR(500) COMMENT '房东电子签名图片路径' AFTER tenant_sign_device,
ADD COLUMN tenant_signature_image VARCHAR(500) COMMENT '租客电子签名图片路径' AFTER landlord_signature_image,
ADD COLUMN contract_snapshot_html VARCHAR(500) COMMENT '合同HTML快照路径' AFTER tenant_signature_image,
ADD COLUMN contract_snapshot_pdf VARCHAR(500) COMMENT '合同PDF快照路径' AFTER contract_snapshot_html,
ADD COLUMN cancelled_at DATETIME COMMENT '取消时间' AFTER terminate_reason,
ADD COLUMN cancel_reason VARCHAR(500) COMMENT '取消原因' AFTER cancelled_at;

-- 2. 修改 contracts 表 status 字段的默认值
ALTER TABLE contracts ALTER COLUMN status SET DEFAULT 'draft';

-- 3. 创建合约申请表
CREATE TABLE IF NOT EXISTS contract_applications (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    booking_id      INT             NOT NULL                  COMMENT '关联的看房记录ID',
    property_id     INT             NOT NULL                  COMMENT '房源ID',
    tenant_id       INT             NOT NULL                  COMMENT '租客ID',
    landlord_id     INT             NOT NULL                  COMMENT '房东ID',
    start_date      DATETIME        NOT NULL                  COMMENT '期望租赁开始日期',
    end_date        DATETIME        NOT NULL                  COMMENT '期望租赁结束日期',
    payment_method  VARCHAR(50)     DEFAULT NULL              COMMENT '付款方式',
    additional_notes TEXT           DEFAULT NULL              COMMENT '补充说明',
    status          VARCHAR(50)     NOT NULL DEFAULT 'apply_pending' COMMENT '申请状态',
    landlord_response TEXT          DEFAULT NULL              COMMENT '房东回复/拒绝原因',
    responded_at    DATETIME        DEFAULT NULL              COMMENT '房东响应时间',
    contract_id     INT             DEFAULT NULL              COMMENT '关联的合同ID',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    cancelled_at    DATETIME        DEFAULT NULL              COMMENT '取消时间',
    
    INDEX idx_booking_id    (booking_id),
    INDEX idx_property_id   (property_id),
    INDEX idx_tenant_id     (tenant_id),
    INDEX idx_landlord_id   (landlord_id),
    INDEX idx_status        (status),
    INDEX idx_contract_id   (contract_id),
    
    CONSTRAINT fk_app_booking FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_app_property FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_app_tenant FOREIGN KEY (tenant_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_app_landlord FOREIGN KEY (landlord_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_app_contract FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合约申请表';

-- 4. 创建合同变更申请表
CREATE TABLE IF NOT EXISTS contract_change_requests (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    contract_id     INT             NOT NULL                  COMMENT '合同ID',
    initiator_id    INT             NOT NULL                  COMMENT '发起人ID',
    change_reason   TEXT            NOT NULL                  COMMENT '变更原因',
    change_fields   JSON            NOT NULL                  COMMENT '变更字段列表',
    status          VARCHAR(50)     NOT NULL DEFAULT 'pending' COMMENT '申请状态',
    responder_id    INT             DEFAULT NULL              COMMENT '响应人ID',
    response_opinion TEXT           DEFAULT NULL              COMMENT '对方处理意见',
    responded_at    DATETIME        DEFAULT NULL              COMMENT '响应时间',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_contract_id   (contract_id),
    INDEX idx_initiator_id  (initiator_id),
    INDEX idx_responder_id  (responder_id),
    INDEX idx_status        (status),
    
    CONSTRAINT fk_change_contract FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_change_initiator FOREIGN KEY (initiator_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_change_responder FOREIGN KEY (responder_id) REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合同变更申请表';

-- 5. 创建合同提前解约申请表
CREATE TABLE IF NOT EXISTS contract_termination_requests (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    contract_id             INT             NOT NULL                  COMMENT '合同ID',
    initiator_id            INT             NOT NULL                  COMMENT '发起人ID',
    termination_reason      TEXT            NOT NULL                  COMMENT '解约原因',
    expected_termination_date DATETIME      NOT NULL                  COMMENT '期望解约日期',
    penalty_amount          FLOAT           DEFAULT NULL              COMMENT '违约金金额',
    deposit_handling        TEXT            DEFAULT NULL              COMMENT '押金处理说明',
    additional_notes        TEXT            DEFAULT NULL              COMMENT '备注',
    status                  VARCHAR(50)     NOT NULL DEFAULT 'pending' COMMENT '申请状态',
    responder_id            INT             DEFAULT NULL              COMMENT '响应人ID',
    response_opinion        TEXT            DEFAULT NULL              COMMENT '对方处理意见',
    responded_at            DATETIME        DEFAULT NULL              COMMENT '响应时间',
    created_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_contract_id   (contract_id),
    INDEX idx_initiator_id  (initiator_id),
    INDEX idx_responder_id  (responder_id),
    INDEX idx_status        (status),
    
    CONSTRAINT fk_term_contract FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_term_initiator FOREIGN KEY (initiator_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_term_responder FOREIGN KEY (responder_id) REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合同提前解约申请表';

-- 6. 数据迁移：将现有合同状态映射到新状态
UPDATE contracts SET status = 'draft' WHERE status = 'pending_sign' AND signed_by_landlord = 0 AND signed_by_tenant = 0;
UPDATE contracts SET status = 'part_signed' WHERE status IN ('pending_landlord_sign', 'pending_tenant_sign');
UPDATE contracts SET status = 'active' WHERE status = 'active';
UPDATE contracts SET status = 'terminated' WHERE status = 'terminated';
UPDATE contracts SET status = 'cancelled' WHERE status = 'cancelled';
UPDATE contracts SET status = 'expired' WHERE status = 'expired';

-- ============================================================
-- 迁移完成提示
-- ============================================================
-- 请检查以上SQL执行结果，确保所有表和字段创建成功
-- 建议在执行前备份数据库
