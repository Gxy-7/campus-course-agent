SET NAMES utf8mb4;

-- 课程课表表
CREATE TABLE IF NOT EXISTS `course_schedules` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `course_id` int NOT NULL COMMENT '课程ID',
  `weekday` int NOT NULL COMMENT '星期：1-7',
  `start_section` int NOT NULL COMMENT '开始节次',
  `end_section` int NOT NULL COMMENT '结束节次',
  `start_week` int NOT NULL COMMENT '开始周',
  `end_week` int NOT NULL COMMENT '结束周',
  `week_type` int NOT NULL DEFAULT 0 COMMENT '周类型：0-每周，1-单周，2-双周',
  `classroom` varchar(100) NOT NULL COMMENT '上课地点',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_course_schedule`
    (`course_id`, `weekday`, `start_section`, `start_week`, `week_type`),
  KEY `ix_course_schedules_course_id` (`course_id`),
  CONSTRAINT `fk_course_schedules_course`
    FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程课表';

-- CS101 数据结构：周一 1-2 节、周三 3-4 节
INSERT IGNORE INTO `course_schedules`
  (`course_id`, `weekday`, `start_section`, `end_section`, `start_week`, `end_week`, `week_type`, `classroom`, `create_time`, `update_time`)
SELECT `id`, 1, 1, 2, 1, 16, 0, 'A101', NOW(), NOW()
FROM `courses` WHERE `code` = 'CS101';

INSERT IGNORE INTO `course_schedules`
  (`course_id`, `weekday`, `start_section`, `end_section`, `start_week`, `end_week`, `week_type`, `classroom`, `create_time`, `update_time`)
SELECT `id`, 3, 3, 4, 1, 16, 0, 'A101', NOW(), NOW()
FROM `courses` WHERE `code` = 'CS101';

-- CS102 计算机网络：周二 3-4 节、周四 5-6 节
INSERT IGNORE INTO `course_schedules`
  (`course_id`, `weekday`, `start_section`, `end_section`, `start_week`, `end_week`, `week_type`, `classroom`, `create_time`, `update_time`)
SELECT `id`, 2, 3, 4, 1, 16, 0, 'B202', NOW(), NOW()
FROM `courses` WHERE `code` = 'CS102';

INSERT IGNORE INTO `course_schedules`
  (`course_id`, `weekday`, `start_section`, `end_section`, `start_week`, `end_week`, `week_type`, `classroom`, `create_time`, `update_time`)
SELECT `id`, 4, 5, 6, 1, 16, 0, 'B202', NOW(), NOW()
FROM `courses` WHERE `code` = 'CS102';

-- CS103 人工智能导论：周五 1-2 节
INSERT IGNORE INTO `course_schedules`
  (`course_id`, `weekday`, `start_section`, `end_section`, `start_week`, `end_week`, `week_type`, `classroom`, `create_time`, `update_time`)
SELECT `id`, 5, 1, 2, 1, 16, 0, 'C303', NOW(), NOW()
FROM `courses` WHERE `code` = 'CS103';
