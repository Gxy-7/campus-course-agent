SET NAMES utf8mb4;

-- 学生选课关系表
CREATE TABLE IF NOT EXISTS `course_enrollments` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `course_id` int NOT NULL COMMENT '课程ID',
  `student_id` int NOT NULL COMMENT '学生ID',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_course_enrollment` (`course_id`, `student_id`),
  KEY `ix_course_enrollments_course_id` (`course_id`),
  KEY `ix_course_enrollments_student_id` (`student_id`),
  CONSTRAINT `fk_course_enrollments_course`
    FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_course_enrollments_student`
    FOREIGN KEY (`student_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='学生选课关系';

-- 给演示学生初始化不冲突的课程
INSERT IGNORE INTO `course_enrollments`
  (`course_id`, `student_id`, `create_time`, `update_time`)
SELECT c.id, u.id, NOW(), NOW()
FROM `courses` c
JOIN `users` u ON u.username = 'aaa'
WHERE c.code = 'CS101';

INSERT IGNORE INTO `course_enrollments`
  (`course_id`, `student_id`, `create_time`, `update_time`)
SELECT c.id, u.id, NOW(), NOW()
FROM `courses` c
JOIN `users` u ON u.username = 'aaa'
WHERE c.code = 'CS102';

INSERT IGNORE INTO `course_enrollments`
  (`course_id`, `student_id`, `create_time`, `update_time`)
SELECT c.id, u.id, NOW(), NOW()
FROM `courses` c
JOIN `users` u ON u.username = 'bbb'
WHERE c.code = 'CS103';
