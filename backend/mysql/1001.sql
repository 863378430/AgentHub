CREATE DATABASE IF NOT EXISTS agent DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE agent;

# 创建简化的用户权限表
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    email VARCHAR(100) NOT NULL UNIQUE COMMENT '登录邮箱',
    password VARCHAR(255) NOT NULL COMMENT '加密密码',
    role VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '角色：admin/user/guest',
    permissions VARCHAR(500) DEFAULT '' COMMENT '权限编码，逗号分隔',
    status TINYINT DEFAULT 1 COMMENT '1-启用 0-禁用',
    last_login_at DATETIME NULL COMMENT '最后登录时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) COMMENT '用户权限合一表';

# 插入测试数据（密码123456）
INSERT INTO users (username, email, password, role, permissions) VALUES 
('admin', 'admin@example.com', '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'admin', 'user:manage,content:view,content:edit,system:setting'),
('test_user', 'user@example.com', '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'user', 'content:view,content:edit'),
('test_guest', 'guest@example.com', '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'guest', 'content:view');