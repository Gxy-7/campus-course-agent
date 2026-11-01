SET NAMES utf8mb4;

-- 学习计划表：只保存计划本身，任务清单后续再加
CREATE TABLE IF NOT EXISTS `study_plans` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `student_id` int NOT NULL COMMENT '学生ID',
  `title` varchar(100) NOT NULL COMMENT '计划标题',
  `goal` text NULL COMMENT '学习目标',
  `start_date` date NOT NULL COMMENT '开始日期',
  `end_date` date NOT NULL COMMENT '结束日期',
  `status` int NOT NULL DEFAULT 0 COMMENT '状态：0-进行中，1-已完成',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `ix_study_plans_student_id` (`student_id`),
  CONSTRAINT `fk_study_plans_student`
    FOREIGN KEY (`student_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学习计划';

-- 给 aaa 初始化一个演示计划，重复执行不会重复插入
INSERT INTO `study_plans`
  (`student_id`, `title`, `goal`, `start_date`, `end_date`, `status`, `create_time`, `update_time`)
SELECT u.id, '期末复习计划', '复习数据结构和计算机网络，准备期末考试。',
       '2026-11-01', '2026-11-20', 0, NOW(), NOW()
FROM `users` u
WHERE u.username = 'aaa'
  AND NOT EXISTS (
    SELECT 1 FROM `study_plans` p
    WHERE p.student_id = u.id AND p.title = '期末复习计划'
  );
