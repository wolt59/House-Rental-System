-- ============================================================
-- 智能房屋租赁系统 - MySQL 数据库完整建表脚本
-- 数据库: house_rental
-- 字符集: utf8mb4
-- ============================================================

CREATE DATABASE IF NOT EXISTS house_rental
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE house_rental;

-- ============================================================
-- 1. 用户表
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(80)     NOT NULL,
    email           VARCHAR(120)    NOT NULL,
    phone           VARCHAR(30)     DEFAULT NULL,
    full_name       VARCHAR(120)    DEFAULT NULL,
    avatar_url      VARCHAR(500)    DEFAULT NULL,
    hashed_password VARCHAR(255)    NOT NULL,
    role            VARCHAR(30)     NOT NULL DEFAULT 'tenant'  COMMENT 'tenant/landlord/admin',
    is_active       TINYINT(1)      NOT NULL DEFAULT 1,
    id_card_number  VARCHAR(30)     DEFAULT NULL              COMMENT '身份证号',
    last_login_at   DATETIME        DEFAULT NULL,
    last_login_ip   VARCHAR(45)     DEFAULT NULL,
    remark          VARCHAR(500)    DEFAULT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_username (username),
    UNIQUE KEY uk_email    (email),
    UNIQUE KEY uk_phone    (phone),
    INDEX idx_role         (role),
    INDEX idx_is_active    (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================================
-- 2. 房源表
-- ============================================================
CREATE TABLE IF NOT EXISTS properties (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    owner_id                INT             NOT NULL,
    title                   VARCHAR(200)    NOT NULL,
    address                 VARCHAR(300)    NOT NULL,
    community_name          VARCHAR(200)    DEFAULT NULL              COMMENT '小区名称',
    region                  VARCHAR(100)    DEFAULT NULL              COMMENT '区域/商圈',
    city                    VARCHAR(50)     DEFAULT NULL              COMMENT '所属城市',
    property_type           VARCHAR(50)     DEFAULT NULL              COMMENT '房屋类型: 公寓/别墅/商住等',
    rental_type             VARCHAR(50)     DEFAULT NULL              COMMENT '房源类型: 整租/合租/公寓/商铺',
    floor_plan              VARCHAR(50)     DEFAULT NULL              COMMENT '户型: 2室1厅',
    bedrooms                INT             DEFAULT NULL              COMMENT '卧室数量',
    livingrooms             INT             DEFAULT NULL              COMMENT '客厅数量',
    bathrooms               INT             DEFAULT NULL              COMMENT '卫生间数量',
    area                    FLOAT           DEFAULT NULL              COMMENT '建筑面积(㎡)',
    building_area           FLOAT           DEFAULT NULL              COMMENT '建筑面积(㎡)',
    usable_area             FLOAT           DEFAULT NULL              COMMENT '实用面积(㎡)',
    build_year              INT             DEFAULT NULL              COMMENT '建筑建成年代',
    has_elevator            TINYINT(1)      DEFAULT NULL              COMMENT '电梯配置: 0=无, 1=有',
    total_households        INT             DEFAULT NULL              COMMENT '总户数',
    property_management_type VARCHAR(100)   DEFAULT NULL              COMMENT '物业类型',
    rent                    FLOAT           NOT NULL                  COMMENT '月租金',
    deposit                 FLOAT           DEFAULT NULL              COMMENT '押金',
    payment_method          VARCHAR(50)     DEFAULT NULL              COMMENT '付款方式: 押一付一/押一付三/半年付/年付',
    min_lease_term          INT             DEFAULT NULL              COMMENT '最短租期(月)',
    earliest_move_in_date   DATE            DEFAULT NULL              COMMENT '最早可入住时间',
    property_fee_bearer     VARCHAR(50)     DEFAULT NULL              COMMENT '物业费承担方: 房东/租客',
    utility_fee_bearer      VARCHAR(100)    DEFAULT NULL              COMMENT '水电燃气费承担方',
    other_fee_bearer        VARCHAR(200)    DEFAULT NULL              COMMENT '网络、垃圾清运等其他费用承担方',
    allow_pets              TINYINT(1)      DEFAULT 0                 COMMENT '是否允许饲养宠物: 0=否, 1=是',
    decoration              VARCHAR(100)    DEFAULT NULL              COMMENT '装修情况',
    orientation             VARCHAR(50)     DEFAULT NULL              COMMENT '朝向: 南/南北等',
    floor_number            VARCHAR(20)     DEFAULT NULL              COMMENT '楼层: 如 5/18',
    total_floors            INT             DEFAULT NULL              COMMENT '总楼层数',
    facilities              VARCHAR(500)    DEFAULT NULL              COMMENT '配套设施 JSON',
    surrounding             TEXT            DEFAULT NULL              COMMENT '周边环境描述',
    viewing_time_rules      VARCHAR(500)    DEFAULT NULL              COMMENT '日常可接待看房的时间段',
    video_url               VARCHAR(500)    DEFAULT NULL              COMMENT '视频链接',
    latitude                FLOAT           DEFAULT NULL              COMMENT '纬度',
    longitude               FLOAT           DEFAULT NULL              COMMENT '经度',
    view_count              INT             NOT NULL DEFAULT 0        COMMENT '浏览量',
    status                  VARCHAR(50)     NOT NULL DEFAULT 'unpublished' COMMENT 'published/vacant/rented/maintenance/unpublished',
    review_status           VARCHAR(30)     NOT NULL DEFAULT 'draft'  COMMENT 'draft/pending/reviewing/approved/rejected',
    review_comment          VARCHAR(500)    DEFAULT NULL              COMMENT '审核意见',
    submitted_at            DATETIME        DEFAULT NULL              COMMENT '提交审核时间',
    approved_at             DATETIME        DEFAULT NULL              COMMENT '审核通过时间',
    published_at            DATETIME        DEFAULT NULL              COMMENT '发布时间',
    unpublished_at          DATETIME        DEFAULT NULL              COMMENT '暂停发布时间',
    description             TEXT            DEFAULT NULL              COMMENT '房源描述',
    tags                    VARCHAR(500)    DEFAULT NULL              COMMENT '特色标签: 近地铁/拎包入住/采光好等(逗号分隔)',
    landlord_notes          TEXT            DEFAULT NULL              COMMENT '房东额外说明、特殊要求等',
    created_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_owner_id      (owner_id),
    INDEX idx_region        (region),
    INDEX idx_floor_plan    (floor_plan),
    INDEX idx_status        (status),
    INDEX idx_review_status (review_status),
    INDEX idx_rent          (rent),
    INDEX idx_submitted_at  (submitted_at),
    INDEX idx_published_at  (published_at),

    CONSTRAINT fk_property_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='房源表';

-- ============================================================
-- 3. 房源图片表
-- ============================================================
CREATE TABLE IF NOT EXISTS property_images (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    property_id     INT             NOT NULL,
    image_url       VARCHAR(500)    NOT NULL,
    image_type      VARCHAR(20)     NOT NULL DEFAULT 'photo'  COMMENT 'photo/video',
    is_cover        TINYINT         NOT NULL DEFAULT 0        COMMENT '是否封面: 0否 1是',
    sort_order      INT             NOT NULL DEFAULT 0        COMMENT '排序序号',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_property_id   (property_id),

    CONSTRAINT fk_image_property FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='房源图片表';

-- ============================================================
-- 4. 预约看房表
-- ============================================================
CREATE TABLE IF NOT EXISTS bookings (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id               INT             NOT NULL,
    property_id             INT             NOT NULL,
    appointment_time        DATETIME        NOT NULL                  COMMENT '预约时间',
    status                  VARCHAR(50)     NOT NULL DEFAULT 'pending' COMMENT 'pending/approved/rejected/cancelled/completed',
    cancel_reason           VARCHAR(500)    DEFAULT NULL              COMMENT '取消原因',
    reject_reason           VARCHAR(500)    DEFAULT NULL              COMMENT '拒绝原因',
    reschedule_proposal     TEXT            DEFAULT NULL              COMMENT '改期建议',
    reschedule_response     VARCHAR(50)     DEFAULT NULL              COMMENT '租客对改期的响应',
    confirmed_at            DATETIME        DEFAULT NULL              COMMENT '确认时间',
    completed_at            DATETIME        DEFAULT NULL              COMMENT '看房完成时间',
    landlord_contact_shown  INT             DEFAULT 0                 COMMENT '是否已查看房东联系方式',
    note                    VARCHAR(500)    DEFAULT NULL              COMMENT '备注',
    created_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_tenant_id         (tenant_id),
    INDEX idx_property_id       (property_id),
    INDEX idx_status            (status),
    INDEX idx_appointment       (appointment_time),
    INDEX idx_tenant_status     (tenant_id, status),
    INDEX idx_property_status   (property_id, status),

    CONSTRAINT fk_booking_tenant   FOREIGN KEY (tenant_id)   REFERENCES users(id)      ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_booking_property FOREIGN KEY (property_id)  REFERENCES properties(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预约看房表';

-- ============================================================
-- 5. 合同表
-- ============================================================
CREATE TABLE IF NOT EXISTS contracts (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    contract_no             VARCHAR(50)     DEFAULT NULL              COMMENT '合同编号',
    property_id             INT             NOT NULL,
    landlord_id             INT             NOT NULL,
    tenant_id               INT             NOT NULL,
    start_date              DATETIME        NOT NULL                  COMMENT '租期开始',
    end_date                DATETIME        NOT NULL                  COMMENT '租期结束',
    monthly_rent            FLOAT           NOT NULL                  COMMENT '月租金',
    deposit                 FLOAT           DEFAULT NULL              COMMENT '押金',
    payment_method          VARCHAR(50)     DEFAULT NULL              COMMENT '付款方式',
    payment_day             INT             DEFAULT NULL              COMMENT '每月缴费日(1-28)',
    min_lease_term          INT             DEFAULT NULL              COMMENT '最短租期(月)',
    renewal_notice_days     INT             DEFAULT NULL              COMMENT '续租提醒天数',
    check_in_time           DATETIME        DEFAULT NULL              COMMENT '入住时间',
    allow_pets              INT             DEFAULT 0                 COMMENT '是否允许养宠物: 0=否, 1=是',
    early_termination_days  INT             DEFAULT NULL              COMMENT '解约提前天数',
    property_fee_bearer     VARCHAR(50)     DEFAULT NULL              COMMENT '物业费承担方',
    utility_fee_bearer      VARCHAR(100)    DEFAULT NULL              COMMENT '水电燃气承担方',
    other_fee_bearer        VARCHAR(200)    DEFAULT NULL              COMMENT '其他费用承担方',
    additional_terms        TEXT            DEFAULT NULL              COMMENT '补充约定',
    terms                   TEXT            DEFAULT NULL              COMMENT '合同条款',
    status                  VARCHAR(50)     NOT NULL DEFAULT 'draft'  COMMENT 'draft/part_signed/active/terminated/expired/cancelled',
    signed_by_landlord      TINYINT         NOT NULL DEFAULT 0,
    signed_by_tenant        TINYINT         NOT NULL DEFAULT 0,
    landlord_signed_at      DATETIME        DEFAULT NULL,
    tenant_signed_at        DATETIME        DEFAULT NULL,
    landlord_sign_ip        VARCHAR(45)     DEFAULT NULL              COMMENT '房东签署IP',
    landlord_sign_device    VARCHAR(200)    DEFAULT NULL              COMMENT '房东签署设备信息',
    tenant_sign_ip          VARCHAR(45)     DEFAULT NULL              COMMENT '租客签署IP',
    tenant_sign_device      VARCHAR(200)    DEFAULT NULL              COMMENT '租客签署设备信息',
    landlord_signature_image text   DEFAULT NULL              COMMENT '房东电子签名图片路径',
    tenant_signature_image  text    DEFAULT NULL              COMMENT '租客电子签名图片路径',
    contract_snapshot_html  VARCHAR(500)    DEFAULT NULL              COMMENT '合同HTML快照路径',
    contract_snapshot_pdf   VARCHAR(500)    DEFAULT NULL              COMMENT '合同PDF快照路径',
    terminated_at           DATETIME        DEFAULT NULL,
    terminate_reason        VARCHAR(500)    DEFAULT NULL,
    cancelled_at            DATETIME        DEFAULT NULL              COMMENT '取消时间',
    cancel_reason           VARCHAR(500)    DEFAULT NULL              COMMENT '取消原因',
    remark                  VARCHAR(500)    DEFAULT NULL,
    created_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_contract_no (contract_no),
    INDEX idx_property_id  (property_id),
    INDEX idx_landlord_id  (landlord_id),
    INDEX idx_tenant_id    (tenant_id),
    INDEX idx_status       (status),
    INDEX idx_start_date   (start_date),
    INDEX idx_end_date     (end_date),

    CONSTRAINT fk_contract_property FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_contract_landlord FOREIGN KEY (landlord_id) REFERENCES users(id)      ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_contract_tenant   FOREIGN KEY (tenant_id)   REFERENCES users(id)      ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='租赁合同表';

-- ============================================================
-- 6. 支付记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS payments (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    bill_no         VARCHAR(50)     DEFAULT NULL              COMMENT '账单编号',
    payment_no      VARCHAR(50)     DEFAULT NULL              COMMENT '支付单号',
    contract_id     INT             NOT NULL,
    property_id     INT             DEFAULT NULL              COMMENT '房源ID(冗余)',
    landlord_id     INT             DEFAULT NULL              COMMENT '房东ID(冗余)',
    tenant_id       INT             NOT NULL,
    due_amount      FLOAT           NOT NULL                  COMMENT '应收金额',
    bill_type       VARCHAR(50)     DEFAULT 'rent'            COMMENT '账单类型',
    period          VARCHAR(20)     DEFAULT NULL              COMMENT '所属周期, 如2026-01',
    actual_amount   FLOAT           DEFAULT NULL              COMMENT '实付金额',
    payment_method  VARCHAR(50)     DEFAULT NULL              COMMENT '支付方式: alipay/wechat/bank/cash',
    payment_time    DATETIME        DEFAULT NULL              COMMENT '付款时间',
    payment_proof   VARCHAR(500)    DEFAULT NULL              COMMENT '付款凭证URL',
    transaction_note VARCHAR(500)   DEFAULT NULL              COMMENT '转账备注',
    status          VARCHAR(50)     NOT NULL DEFAULT 'pending' COMMENT 'pending/paid/overdue/cancelled/refunded',
    due_date        DATETIME        DEFAULT NULL              COMMENT '应缴日期',
    paid_at         DATETIME        DEFAULT NULL              COMMENT '实际支付时间',
    confirmed_at    DATETIME        DEFAULT NULL              COMMENT '确认收款时间',
    overdue_days    INT             NOT NULL DEFAULT 0        COMMENT '逾期天数',
    overdue_fee     FLOAT           NOT NULL DEFAULT 0        COMMENT '滞纳金',
    rejected_reason VARCHAR(500)    DEFAULT NULL              COMMENT '驳回原因',
    remark          VARCHAR(500)    DEFAULT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_payment_no   (payment_no),
    UNIQUE KEY uk_bill_no      (bill_no),
    INDEX idx_contract_id (contract_id),
    INDEX idx_tenant_id   (tenant_id),
    INDEX idx_status      (status),
    INDEX idx_due_date    (due_date),

    CONSTRAINT fk_payment_contract FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_payment_tenant   FOREIGN KEY (tenant_id)   REFERENCES users(id)      ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_payment_property FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE SET NULL    ON UPDATE CASCADE,
    CONSTRAINT fk_payment_landlord FOREIGN KEY (landlord_id) REFERENCES users(id)      ON DELETE SET NULL    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='支付记录表';

-- ============================================================
-- 7. 维修申请表
-- ============================================================
CREATE TABLE IF NOT EXISTS maintenance_requests (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    property_id     INT             NOT NULL,
    tenant_id       INT             NOT NULL,
    title           VARCHAR(200)    DEFAULT NULL              COMMENT '维修标题',
    description     TEXT            NOT NULL                  COMMENT '维修描述',
    image_urls      VARCHAR(1000)   DEFAULT NULL              COMMENT '图片URL(JSON数组)',
    priority        VARCHAR(20)     NOT NULL DEFAULT 'normal' COMMENT 'low/normal/high/urgent',
    status          VARCHAR(50)     NOT NULL DEFAULT 'new'    COMMENT 'new/in_progress/resolved/closed',
    assigned_to     VARCHAR(120)    DEFAULT NULL              COMMENT '处理人',
    completed_at    DATETIME        DEFAULT NULL              COMMENT '完成时间',
    feedback        VARCHAR(500)    DEFAULT NULL              COMMENT '租客反馈',
    remark          VARCHAR(500)    DEFAULT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_property_id  (property_id),
    INDEX idx_tenant_id    (tenant_id),
    INDEX idx_status       (status),
    INDEX idx_priority     (priority),

    CONSTRAINT fk_maintenance_property FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_maintenance_tenant   FOREIGN KEY (tenant_id)   REFERENCES users(id)      ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='维修申请表';

-- ============================================================
-- 8. 投诉表
-- ============================================================
CREATE TABLE IF NOT EXISTS complaints (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    property_id     INT             NOT NULL,
    tenant_id       INT             NOT NULL,
    complaint_type  VARCHAR(50)     DEFAULT NULL              COMMENT '投诉类型: 房源/服务/其他',
    title           VARCHAR(200)    DEFAULT NULL,
    content         TEXT            NOT NULL,
    image_urls      VARCHAR(1000)   DEFAULT NULL              COMMENT '图片URL(JSON数组)',
    status          VARCHAR(50)     NOT NULL DEFAULT 'open'   COMMENT 'open/in_progress/resolved/closed',
    handled_by      VARCHAR(120)    DEFAULT NULL              COMMENT '处理人',
    result          TEXT            DEFAULT NULL              COMMENT '处理结果',
    resolved_at     DATETIME        DEFAULT NULL,
    remark          VARCHAR(500)    DEFAULT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_property_id    (property_id),
    INDEX idx_tenant_id      (tenant_id),
    INDEX idx_status         (status),
    INDEX idx_complaint_type (complaint_type),

    CONSTRAINT fk_complaint_property FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_complaint_tenant   FOREIGN KEY (tenant_id)   REFERENCES users(id)      ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='投诉表';

-- ============================================================
-- 9. 消息表
-- ============================================================
CREATE TABLE IF NOT EXISTS messages (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    from_user_id    INT             NOT NULL,
    to_user_id      INT             NOT NULL,
    property_id     INT             DEFAULT NULL,
    message_type    VARCHAR(30)     NOT NULL DEFAULT 'text'   COMMENT 'text/system/notification',
    content         VARCHAR(5000)   NOT NULL                  COMMENT '消息内容',
    link            VARCHAR(500)    DEFAULT NULL              COMMENT '链接',
    is_read         TINYINT(1)      NOT NULL DEFAULT 0,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_from_user      (from_user_id),
    INDEX idx_to_user        (to_user_id),
    INDEX idx_property_id    (property_id),
    INDEX idx_is_read        (to_user_id, is_read),
    INDEX idx_created_at     (created_at),
    INDEX idx_message_type   (message_type),
    INDEX idx_from_to        (from_user_id, to_user_id),
    INDEX idx_to_from_read   (to_user_id, from_user_id, is_read),

    CONSTRAINT fk_message_from    FOREIGN KEY (from_user_id) REFERENCES users(id)      ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_message_to      FOREIGN KEY (to_user_id)   REFERENCES users(id)      ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_message_property FOREIGN KEY (property_id)  REFERENCES properties(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息表';

-- ============================================================
-- 10. 新闻表
-- ============================================================
CREATE TABLE IF NOT EXISTS news (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    author_id       INT             NOT NULL,
    title           VARCHAR(200)    NOT NULL,
    content         TEXT            NOT NULL,
    category        VARCHAR(50)     DEFAULT NULL              COMMENT '分类: 租赁资讯/维修通知/政策法规',
    cover_image     VARCHAR(500)    DEFAULT NULL,
    status          VARCHAR(50)     NOT NULL DEFAULT 'draft'  COMMENT 'draft/published/archived',
    review_message  TEXT            DEFAULT NULL              COMMENT '审核意见(拒绝原因等)',
    view_count      INT             NOT NULL DEFAULT 0,
    published_at    DATETIME        DEFAULT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_author_id   (author_id),
    INDEX idx_status      (status),
    INDEX idx_category    (category),
    INDEX idx_published   (published_at),

    CONSTRAINT fk_news_author FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='新闻表';

-- ============================================================
-- 11. 审计日志表
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT             DEFAULT NULL             COMMENT '操作用户ID, 系统操作为NULL',
    action          VARCHAR(200)    NOT NULL,
    target_type     VARCHAR(100)    NOT NULL                 COMMENT '操作对象类型',
    target_id       INT             DEFAULT NULL             COMMENT '操作对象ID',
    detail          TEXT            DEFAULT NULL,
    ip_address      VARCHAR(45)     DEFAULT NULL,
    user_agent      VARCHAR(500)    DEFAULT NULL             COMMENT '浏览器UA',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_user_id      (user_id),
    INDEX idx_action       (action),
    INDEX idx_target       (target_type, target_id),
    INDEX idx_created_at   (created_at),

    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审计日志表';

-- ============================================================
-- 12. 合约申请表
-- ============================================================
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

    CONSTRAINT fk_app_booking  FOREIGN KEY (booking_id)  REFERENCES bookings(id)   ON DELETE CASCADE   ON UPDATE CASCADE,
    CONSTRAINT fk_app_property FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE   ON UPDATE CASCADE,
    CONSTRAINT fk_app_tenant   FOREIGN KEY (tenant_id)   REFERENCES users(id)      ON DELETE CASCADE   ON UPDATE CASCADE,
    CONSTRAINT fk_app_landlord FOREIGN KEY (landlord_id) REFERENCES users(id)      ON DELETE CASCADE   ON UPDATE CASCADE,
    CONSTRAINT fk_app_contract FOREIGN KEY (contract_id) REFERENCES contracts(id)  ON DELETE SET NULL  ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合约申请表';

-- ============================================================
-- 13. 合同变更申请表
-- ============================================================
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

    CONSTRAINT fk_change_contract   FOREIGN KEY (contract_id)  REFERENCES contracts(id) ON DELETE CASCADE   ON UPDATE CASCADE,
    CONSTRAINT fk_change_initiator  FOREIGN KEY (initiator_id) REFERENCES users(id)     ON DELETE CASCADE   ON UPDATE CASCADE,
    CONSTRAINT fk_change_responder  FOREIGN KEY (responder_id) REFERENCES users(id)     ON DELETE SET NULL  ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合同变更申请表';

-- ============================================================
-- 14. 合同提前解约申请表
-- ============================================================
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

    CONSTRAINT fk_term_contract   FOREIGN KEY (contract_id)  REFERENCES contracts(id) ON DELETE CASCADE   ON UPDATE CASCADE,
    CONSTRAINT fk_term_initiator  FOREIGN KEY (initiator_id) REFERENCES users(id)     ON DELETE CASCADE   ON UPDATE CASCADE,
    CONSTRAINT fk_term_responder  FOREIGN KEY (responder_id) REFERENCES users(id)     ON DELETE SET NULL  ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='合同提前解约申请表';

-- ============================================================
-- 初始数据: 插入管理员账号 (密码: admin123)
-- ============================================================
INSERT INTO users (username, email, phone, full_name, hashed_password, role, is_active)
VALUES ('admin', 'admin@house-rental.com', '13800000000', '系统管理员',
        '$2b$12$OTNhqDtytL9DXoBYHp2PK.zz4O9LgVjtW5JfS3YDNz.MyNuOi1LPK',
        'admin', 1)
ON DUPLICATE KEY UPDATE username=username;
