-- 1. 创建agent数据库（指定字符集，避免中文乱码）
CREATE DATABASE IF NOT EXISTS agent DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 切换到agent数据库
USE agent;

-- 3. 创建对话主表
DROP TABLE IF EXISTS `chat_conversation`;
CREATE TABLE `chat_conversation` (
  `conversation_id` char(16) NOT NULL COMMENT '16位聊天对话ID（唯一标识）',
  `username` varchar(50) NOT NULL COMMENT '用户名（用户标识）',
  `title` varchar(100) DEFAULT '' COMMENT '对话标题（可选，比如取第一条消息内容）',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '对话创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '对话最后更新时间',
  `is_deleted` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否删除（0=未删，1=已删）',
  PRIMARY KEY (`conversation_id`),
  KEY `idx_username` (`username`) COMMENT '用户名索引，便于查询用户所有对话'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能体聊天对话主表';

-- 4. 创建消息详情表
DROP TABLE IF EXISTS `chat_message`;
CREATE TABLE `chat_message` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '消息自增主键',
  `conversation_id` char(16) NOT NULL COMMENT '关联的16位对话ID',
  `username` varchar(50) NOT NULL COMMENT '发送消息的用户名',
  `role` varchar(20) NOT NULL COMMENT '消息角色（user=用户，assistant=智能体）',
  `content` text NOT NULL COMMENT '聊天消息内容',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '消息发送时间',
  `is_deleted` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否删除（0=未删，1=已删）',
  PRIMARY KEY (`id`),
  KEY `idx_conversation_id` (`conversation_id`) COMMENT '对话ID索引，便于查询单对话的所有消息',
  KEY `idx_create_time` (`create_time`) COMMENT '时间索引，便于按时间排序消息'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能体聊天消息详情表';

-- 5. 插入测试对话数据（16位对话ID：2026031600000001）
INSERT INTO `chat_conversation` (`conversation_id`, `username`, `title`) 
VALUES ('2026031600000001', 'test_user', '智能体功能咨询');

-- 6. 插入测试聊天记录
-- 用户发送的消息
INSERT INTO `chat_message` (`conversation_id`, `username`, `role`, `content`) 
VALUES ('2026031600000001', 'test_user', 'user', '你好，智能体怎么使用？');
-- 智能体回复的消息
INSERT INTO `chat_message` (`conversation_id`, `username`, `role`, `content`) 
VALUES ('2026031600000001', 'test_user', 'assistant', '你可以通过发送指令的方式调用智能体，比如输入“帮我写SQL”，也可以结合业务场景定制指令');

-- 7. 验证数据（查询测试）
SELECT c.conversation_id, c.username, m.role, m.content 
FROM chat_conversation c
LEFT JOIN chat_message m ON c.conversation_id = m.conversation_id
WHERE c.conversation_id = '2026031600000001';