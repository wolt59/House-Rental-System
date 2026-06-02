-- 新闻系统增强：添加审核流程
-- 为 news 表添加 review_message 字段，支持管理员审核

ALTER TABLE `news`
  ADD COLUMN `review_message` TEXT NULL COMMENT '审核意见（拒绝原因等）' AFTER `status`;

-- 更新现有已发布新闻的状态（兼容已有数据）
-- 如果已有 published 的新闻，保持不变即可
