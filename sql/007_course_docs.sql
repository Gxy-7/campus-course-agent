SET NAMES utf8mb4;

-- 课程资料元数据
CREATE TABLE IF NOT EXISTS `course_documents` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `course_id` int NOT NULL COMMENT '课程ID',
  `title` varchar(150) NOT NULL COMMENT '资料标题',
  `original_name` varchar(255) NOT NULL COMMENT '原始文件名',
  `disk_name` varchar(255) NOT NULL COMMENT '磁盘文件名',
  `file_type` varchar(20) NOT NULL COMMENT '文件类型',
  `char_count` int NOT NULL DEFAULT 0 COMMENT '字符数',
  `chunk_count` int NOT NULL DEFAULT 0 COMMENT '文本块数量',
  `uploaded_by` int NULL COMMENT '上传人ID',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `ix_course_documents_course_id` (`course_id`),
  CONSTRAINT `fk_course_documents_course`
    FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_course_documents_user`
    FOREIGN KEY (`uploaded_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程资料';

-- 课程资料文本块，检索时使用
CREATE TABLE IF NOT EXISTS `course_doc_chunks` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `document_id` int NOT NULL COMMENT '资料ID',
  `chunk_index` int NOT NULL COMMENT '块序号',
  `content` text NOT NULL COMMENT '文本内容',
  `source_page` int NULL COMMENT 'PDF页码',
  `create_time` datetime NOT NULL COMMENT '创建时间',
  `update_time` datetime NOT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `ix_course_doc_chunks_document_id` (`document_id`),
  CONSTRAINT `fk_course_doc_chunks_document`
    FOREIGN KEY (`document_id`) REFERENCES `course_documents` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='课程资料文本块';
