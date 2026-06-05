-- ============================================================
-- 消息系统重构 - 数据库迁移脚本
-- 变更内容:
--   1. 扩展 messages.content 字段长度 1000 -> 5000
--   2. 添加 message_type 和 is_read 索引优化查询
--   3. 添加复合索引 (from_user_id, to_user_id) 加速会话查询
-- ============================================================

ALTER TABLE messages
    MODIFY COLUMN content VARCHAR(5000) NOT NULL COMMENT '消息内容(扩展到5000字符)';

ALTER TABLE messages
    ADD INDEX idx_message_type (message_type);

ALTER TABLE messages
    ADD INDEX idx_from_to (from_user_id, to_user_id);

ALTER TABLE messages
    ADD INDEX idx_to_from_read (to_user_id, from_user_id, is_read);

ALTER TABLE messages ADD COLUMN link VARCHAR(500) NULL;