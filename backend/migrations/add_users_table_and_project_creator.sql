-- ============================================================
-- 添加用户表和项目创建人字段
-- ============================================================
-- 本脚本用于：
-- 1. 创建用户表（users）
-- 2. 在项目表中添加创建人字段（creator_id）
-- ============================================================

-- 1. 创建用户表
IF OBJECT_ID('users', 'U') IS NOT NULL
    DROP TABLE users;
GO

CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    username NVARCHAR(50) NOT NULL UNIQUE,
    password_hash NVARCHAR(MAX) NULL,
    name NVARCHAR(100) NOT NULL,
    role NVARCHAR(20) NOT NULL CHECK (role IN ('admin', 'user')) DEFAULT 'user',
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
GO

-- 创建索引
CREATE INDEX IX_users_username ON users(username);
GO

-- 添加注释
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'用户表：存储系统用户信息，用于登录和权限控制。密码字段为明文存储，可选。', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'users';
GO

-- 2. 在项目表中添加创建人字段
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('projects') AND name = 'creator_id')
BEGIN
    ALTER TABLE projects
    ADD creator_id INT NULL;
    
    -- 创建外键约束
    ALTER TABLE projects
    ADD CONSTRAINT FK_projects_creator FOREIGN KEY (creator_id) 
        REFERENCES users(id) ON DELETE SET NULL;
    
    -- 创建索引
    CREATE INDEX IX_projects_creator_id ON projects(creator_id);
    
    PRINT N'已添加项目表的创建人字段';
END
ELSE
BEGIN
    PRINT N'项目表的创建人字段已存在';
END
GO

-- 3. 创建默认管理员账户（密码：admin123，明文存储）
DECLARE @admin_password NVARCHAR(MAX) = N'admin123'; -- 明文密码

-- 检查是否已有管理员账户
IF NOT EXISTS (SELECT 1 FROM users WHERE username = 'admin')
BEGIN
    INSERT INTO users (username, password_hash, name, role, is_active)
    VALUES (N'admin', @admin_password, N'系统管理员', 'admin', 1);
    PRINT N'已创建默认管理员账户（用户名：admin，密码：admin123）';
    PRINT N'注意：请在生产环境中修改默认密码！';
END
ELSE
BEGIN
    PRINT N'管理员账户已存在';
END
GO

PRINT N'用户表和项目创建人字段创建完成！';
GO

