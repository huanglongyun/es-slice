CREATE DATABASE IF NOT EXISTS es_slice DEFAULT CHARACTER SET utf8mb4;
USE es_slice;

CREATE TABLE sys_user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    real_name VARCHAR(50),
    email VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'viewer',
    status TINYINT DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE audit_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT,
    username VARCHAR(50),
    action VARCHAR(50),
    index_name VARCHAR(100),
    doc_id VARCHAR(100),
    before_content TEXT,
    after_content TEXT,
    ip_address VARCHAR(50),
    created_at DATETIME
);

-- 默认管理员: admin / admin123
INSERT INTO sys_user (username, password, real_name, role, status, created_at, updated_at)
VALUES ('admin', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7iAt6Z5Eh', '系统管理员', 'admin', 1, NOW(), NOW());
