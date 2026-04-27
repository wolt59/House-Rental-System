-- ============================================================
-- 智能房屋租赁系统 - MySQL 数据库建表脚本
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
    id              INT AUTO_INCREMENT PRIMARY KEY,
    owner_id        INT             NOT NULL,
    title           VARCHAR(200)    NOT NULL,
    address         VARCHAR(300)    NOT NULL,
    region          VARCHAR(100)    DEFAULT NULL              COMMENT '区域/商圈',
    property_type   VARCHAR(50)     DEFAULT NULL              COMMENT '房屋类型: 公寓/别墅/商住等',
    floor_plan      VARCHAR(50)     DEFAULT NULL              COMMENT '户型: 2室1厅',
    area            FLOAT           DEFAULT NULL              COMMENT '建筑面积(㎡)',
    rent            FLOAT           NOT NULL                  COMMENT '月租金',
    deposit         FLOAT           DEFAULT NULL              COMMENT '押金',
    decoration      VARCHAR(100)    DEFAULT NULL              COMMENT '装修情况',
    orientation     VARCHAR(50)     DEFAULT NULL              COMMENT '朝向: 南/南北等',
    floor_number    VARCHAR(20)     DEFAULT NULL              COMMENT '楼层: 如 5/18',
    total_floors    INT             DEFAULT NULL              COMMENT '总楼层数',
    facilities      VARCHAR(500)    DEFAULT NULL              COMMENT '配套设施 JSON',
    surrounding     TEXT            DEFAULT NULL              COMMENT '周边环境描述',
    video_url       VARCHAR(500)    DEFAULT NULL              COMMENT '视频链接',
    latitude        FLOAT           DEFAULT NULL              COMMENT '纬度',
    longitude       FLOAT           DEFAULT NULL              COMMENT '经度',
    view_count      INT             NOT NULL DEFAULT 0        COMMENT '浏览量',
    status          VARCHAR(50)     NOT NULL DEFAULT 'vacant' COMMENT 'vacant/rented/maintenance',
    review_status   VARCHAR(30)     NOT NULL DEFAULT 'pending' COMMENT 'pending/approved/rejected',
    review_comment  VARCHAR(500)    DEFAULT NULL              COMMENT '审核意见',
    description     TEXT            DEFAULT NULL              COMMENT '房源描述',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_owner_id      (owner_id),
    INDEX idx_region        (region),
    INDEX idx_floor_plan    (floor_plan),
    INDEX idx_status        (status),
    INDEX idx_review_status (review_status),
    INDEX idx_rent          (rent),

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
    id              INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id       INT             NOT NULL,
    property_id     INT             NOT NULL,
    appointment_time DATETIME       NOT NULL                  COMMENT '预约时间',
    status          VARCHAR(50)     NOT NULL DEFAULT 'pending' COMMENT 'pending/approved/rejected/cancelled/completed',
    cancel_reason   VARCHAR(500)    DEFAULT NULL              COMMENT '取消原因',
    confirmed_at    DATETIME        DEFAULT NULL              COMMENT '确认时间',
    note            VARCHAR(500)    DEFAULT NULL              COMMENT '备注',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_tenant_id    (tenant_id),
    INDEX idx_property_id  (property_id),
    INDEX idx_status       (status),
    INDEX idx_appointment  (appointment_time),

    CONSTRAINT fk_booking_tenant   FOREIGN KEY (tenant_id)   REFERENCES users(id)      ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_booking_property FOREIGN KEY (property_id)  REFERENCES properties(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预约看房表';

-- ============================================================
-- 5. 合同表
-- ============================================================
CREATE TABLE IF NOT EXISTS contracts (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    contract_no         VARCHAR(50)     DEFAULT NULL              COMMENT '合同编号',
    property_id         INT             NOT NULL,
    landlord_id         INT             NOT NULL,
    tenant_id           INT             NOT NULL,
    start_date          DATETIME        NOT NULL                  COMMENT '租期开始',
    end_date            DATETIME        NOT NULL                  COMMENT '租期结束',
    monthly_rent        FLOAT           NOT NULL                  COMMENT '月租金',
    deposit             FLOAT           DEFAULT NULL              COMMENT '押金',
    payment_day         INT             DEFAULT NULL              COMMENT '每月缴费日(1-28)',
    terms               TEXT            DEFAULT NULL              COMMENT '合同条款',
    status              VARCHAR(50)     NOT NULL DEFAULT 'pending_sign' COMMENT 'pending_sign/pending_tenant_sign/pending_landlord_sign/active/terminated/expired',
    signed_by_landlord  TINYINT         NOT NULL DEFAULT 0,
    signed_by_tenant    TINYINT         NOT NULL DEFAULT 0,
    landlord_signed_at  DATETIME        DEFAULT NULL,
    tenant_signed_at    DATETIME        DEFAULT NULL,
    terminated_at       DATETIME        DEFAULT NULL,
    terminate_reason    VARCHAR(500)    DEFAULT NULL,
    remark              VARCHAR(500)    DEFAULT NULL,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

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
    payment_no      VARCHAR(50)     DEFAULT NULL              COMMENT '支付单号',
    contract_id     INT             NOT NULL,
    tenant_id       INT             NOT NULL,
    amount          FLOAT           NOT NULL                  COMMENT '支付金额',
    payment_method  VARCHAR(50)     DEFAULT NULL              COMMENT '支付方式: alipay/wechat/bank/cash',
    status          VARCHAR(50)     NOT NULL DEFAULT 'pending' COMMENT 'pending/paid/overdue/cancelled/refunded',
    due_date        DATETIME        DEFAULT NULL              COMMENT '应缴日期',
    paid_at         DATETIME        DEFAULT NULL              COMMENT '实际支付时间',
    overdue_days    INT             NOT NULL DEFAULT 0        COMMENT '逾期天数',
    overdue_fee     FLOAT           NOT NULL DEFAULT 0        COMMENT '滞纳金',
    remark          VARCHAR(500)    DEFAULT NULL,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_payment_no (payment_no),
    INDEX idx_contract_id (contract_id),
    INDEX idx_tenant_id   (tenant_id),
    INDEX idx_status      (status),
    INDEX idx_due_date    (due_date),

    CONSTRAINT fk_payment_contract FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_payment_tenant   FOREIGN KEY (tenant_id)   REFERENCES users(id)    ON DELETE RESTRICT ON UPDATE CASCADE
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
    content         VARCHAR(1000)   NOT NULL,
    is_read         TINYINT(1)      NOT NULL DEFAULT 0,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_from_user   (from_user_id),
    INDEX idx_to_user     (to_user_id),
    INDEX idx_property_id (property_id),
    INDEX idx_is_read     (to_user_id, is_read),
    INDEX idx_created_at  (created_at),

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
-- 初始数据: 插入管理员账号 (密码: admin123)
-- ============================================================
INSERT INTO users (username, email, phone, full_name, hashed_password, role, is_active)
VALUES ('admin', 'admin@house-rental.com', '13800000000', '系统管理员',
        '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36Kz7aKdBdCkqy5uLbTLyGm',
        'admin', 1)
ON DUPLICATE KEY UPDATE username=username;
