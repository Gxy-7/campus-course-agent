SET NAMES utf8mb4;

-- ============================================================
-- 课程模块初始化脚本
-- 作用：
-- 1. 新建数据库时创建 courses 表（已存在则跳过）
-- 2. 老数据库缺少 teacher 字段时自动补上
-- 3. 修正 code 字段可空的历史问题
-- 4. 写入 3 条演示课程
-- 注意：执行本脚本不会删除 users 表，也不会影响已有用户数据
-- ============================================================

-- 如果 courses 表不存在，就按最新结构创建
CREATE TABLE IF NOT EXISTS `courses` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` varchar(100) NOT NULL COMMENT '课程名称',
  `code` varchar(50) NOT NULL COMMENT '课程代码',
  `teacher` varchar(50) NULL COMMENT '授课老师',
  `description` text NULL COMMENT '课程简介',
  `status` int NOT NULL DEFAULT 1 COMMENT '状态：0-停用，1-正常',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_courses_code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程信息表';

-- MySQL 不支持 ADD COLUMN IF NOT EXISTS，
-- 这里通过 information_schema 判断 teacher 是否已存在，不存在才添加
DROP PROCEDURE IF EXISTS `add_teacher_column`;
DELIMITER //
CREATE PROCEDURE `add_teacher_column`()
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = 'courses'
      AND column_name = 'teacher'
  ) THEN
    ALTER TABLE `courses`
      ADD COLUMN `teacher` varchar(50) NULL COMMENT '授课老师' AFTER `code`;
  END IF;
END //
DELIMITER ;
CALL `add_teacher_column`();
DROP PROCEDURE `add_teacher_column`;

-- 当前旧表的 code 允许为空，和 ORM 模型不一致；表为空时执行是安全的
ALTER TABLE `courses`
  MODIFY COLUMN `code` varchar(50) NOT NULL COMMENT '课程代码';

-- 写入演示课程；重复执行时按课程代码更新，不会重复插入
INSERT INTO `courses`
  (`name`, `code`, `teacher`, `description`, `status`, `create_time`, `update_time`)
VALUES
  ('数据结构', 'CS101', '张老师', '线性表、树、图、排序与查找等核心数据结构与算法基础。', 1, NOW(), NOW()),
  ('计算机网络', 'CS102', '李老师', 'TCP/IP 协议栈、网络分层、路由与传输层核心机制。', 1, NOW(), NOW()),
  ('人工智能导论', 'CS103', '王老师', '人工智能基本概念、搜索、机器学习与大模型应用入门。', 1, NOW(), NOW())
ON DUPLICATE KEY UPDATE
  `name` = VALUES(`name`),
  `teacher` = VALUES(`teacher`),
  `description` = VALUES(`description`),
  `status` = VALUES(`status`),
  `update_time` = NOW();
