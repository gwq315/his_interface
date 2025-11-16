-- ============================================================
-- SQL Server 2019 数据库完整建表脚本
-- 医院HIS系统接口文档管理系统
-- 数据库名: HIS_Interface
-- ============================================================
-- 说明：
-- 1. 所有存储中文的字段使用 NVARCHAR/NTEXT 类型
-- 2. 包含所有外键约束和索引
-- 3. 包含自动更新时间戳触发器
-- 4. 支持 SQL Server 2019 的 JSON 功能
-- ============================================================

USE master;
GO

-- 如果数据库已存在，删除它（谨慎操作！）
-- DROP DATABASE IF EXISTS HIS_Interface;
-- GO

-- 创建数据库（如果不存在）
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'HIS_Interface')
BEGIN
    CREATE DATABASE HIS_Interface
    COLLATE Chinese_PRC_CI_AS;  -- 使用中文排序规则
END
GO

USE HIS_Interface;
GO

-- ============================================================
-- 1. 项目表 (projects)
-- ============================================================
IF OBJECT_ID('projects', 'U') IS NOT NULL
    DROP TABLE projects;
GO

CREATE TABLE projects (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(200) NOT NULL,
    manager NVARCHAR(100) NOT NULL,
    contact_info NTEXT NOT NULL,
    documents NVARCHAR(MAX) NULL,  -- JSON 格式
    attachments NVARCHAR(MAX) NULL,  -- JSON 格式
    description NTEXT NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
GO

-- 创建索引
CREATE INDEX IX_projects_name ON projects(name);
GO

-- 添加注释
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'项目表：存储项目信息，每个项目可以包含多个接口和字典', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'projects';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'主键ID，自增', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'projects',
    @level2type = N'COLUMN', @level2name = N'id';
GO

EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'项目名称，如''医保接口''、''首页上传''', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'projects',
    @level2type = N'COLUMN', @level2name = N'name';
GO

-- ============================================================
-- 2. 接口表 (interfaces)
-- ============================================================
IF OBJECT_ID('interfaces', 'U') IS NOT NULL
    DROP TABLE interfaces;
GO

CREATE TABLE interfaces (
    id INT IDENTITY(1,1) PRIMARY KEY,
    project_id INT NOT NULL,
    name NVARCHAR(200) NOT NULL,
    code NVARCHAR(100) NOT NULL,  -- 使用 NVARCHAR 支持中文编码
    description NTEXT NULL,
    interface_type NVARCHAR(10) NOT NULL CHECK (interface_type IN ('view', 'api')),
    url NVARCHAR(500) NULL,  -- 使用 NVARCHAR 支持中文路径或参数
    method VARCHAR(10) NULL,
    category NVARCHAR(100) NULL,
    tags NVARCHAR(500) NULL,
    status NVARCHAR(20) NOT NULL DEFAULT 'active',
    input_example NTEXT NULL,
    output_example NTEXT NULL,
    view_definition NTEXT NULL,
    notes NTEXT NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    -- 外键约束
    CONSTRAINT FK_interfaces_project FOREIGN KEY (project_id) 
        REFERENCES projects(id) ON DELETE CASCADE,
    
    -- 唯一约束
    CONSTRAINT UQ_interfaces_code UNIQUE (code)
);
GO

-- 创建索引
CREATE INDEX IX_interfaces_project_id ON interfaces(project_id);
CREATE INDEX IX_interfaces_code ON interfaces(code);
GO

-- 添加注释
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'接口表：存储医院HIS系统的接口信息，包括视图接口和API接口', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'interfaces';
GO

-- ============================================================
-- 3. 字典表 (dictionaries)
-- ============================================================
IF OBJECT_ID('dictionaries', 'U') IS NOT NULL
    DROP TABLE dictionaries;
GO

CREATE TABLE dictionaries (
    id INT IDENTITY(1,1) PRIMARY KEY,
    project_id INT NOT NULL,
    name NVARCHAR(200) NOT NULL,
    code NVARCHAR(100) NOT NULL,  -- 使用 NVARCHAR 支持中文编码
    description NTEXT NULL,
    interface_id INT NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    -- 外键约束
    CONSTRAINT FK_dictionaries_project FOREIGN KEY (project_id) 
        REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT FK_dictionaries_interface FOREIGN KEY (interface_id) 
        REFERENCES interfaces(id) ON DELETE NO ACTION,  -- 改为 NO ACTION 避免级联路径冲突
    
    -- 唯一约束
    CONSTRAINT UQ_dictionaries_code UNIQUE (code)
);
GO

-- 创建索引
CREATE INDEX IX_dictionaries_project_id ON dictionaries(project_id);
CREATE INDEX IX_dictionaries_code ON dictionaries(code);
GO

-- 添加注释
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'字典表：存储字典定义信息，用于定义参数的取值范围', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'dictionaries';
GO

-- ============================================================
-- 4. 参数表 (parameters)
-- ============================================================
IF OBJECT_ID('parameters', 'U') IS NOT NULL
    DROP TABLE parameters;
GO

CREATE TABLE parameters (
    id INT IDENTITY(1,1) PRIMARY KEY,
    interface_id INT NOT NULL,
    name NVARCHAR(200) NOT NULL,
    field_name NVARCHAR(100) NOT NULL,
    data_type NVARCHAR(50) NOT NULL,
    param_type NVARCHAR(10) NOT NULL CHECK (param_type IN ('input', 'output')),
    required BIT NOT NULL DEFAULT 0,
    default_value NVARCHAR(500) NULL,
    description NTEXT NULL,
    example NVARCHAR(500) NULL,
    order_index INT NOT NULL DEFAULT 0,
    dictionary_id INT NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    -- 外键约束
    CONSTRAINT FK_parameters_interface FOREIGN KEY (interface_id) 
        REFERENCES interfaces(id) ON DELETE CASCADE,
    CONSTRAINT FK_parameters_dictionary FOREIGN KEY (dictionary_id) 
        REFERENCES dictionaries(id) ON DELETE NO ACTION  -- 改为 NO ACTION 避免级联路径冲突
);
GO

-- 创建索引
CREATE INDEX IX_parameters_interface_id ON parameters(interface_id);
CREATE INDEX IX_parameters_dictionary_id ON parameters(dictionary_id);
GO

-- 添加注释
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'参数表：存储接口的输入参数和输出参数信息', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'parameters';
GO

-- ============================================================
-- 5. 字典值表 (dictionary_values)
-- ============================================================
IF OBJECT_ID('dictionary_values', 'U') IS NOT NULL
    DROP TABLE dictionary_values;
GO

CREATE TABLE dictionary_values (
    id INT IDENTITY(1,1) PRIMARY KEY,
    dictionary_id INT NOT NULL,
    [key] NVARCHAR(100) NOT NULL,  -- key 是保留字，需要用方括号括起来
    value NVARCHAR(500) NOT NULL,
    description NTEXT NULL,
    order_index INT NOT NULL DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    -- 外键约束
    CONSTRAINT FK_dictionary_values_dictionary FOREIGN KEY (dictionary_id) 
        REFERENCES dictionaries(id) ON DELETE CASCADE
);
GO

-- 创建索引
CREATE INDEX IX_dictionary_values_dictionary_id ON dictionary_values(dictionary_id);
GO

-- 添加注释
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'字典值表：存储字典的键值对信息', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'dictionary_values';
GO

-- ============================================================
-- 6. 文档表 (documents)
-- ============================================================
IF OBJECT_ID('documents', 'U') IS NOT NULL
    DROP TABLE documents;
GO

CREATE TABLE documents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    title NVARCHAR(200) NOT NULL,
    description NTEXT NULL,
    region NVARCHAR(50) NULL,
    person NVARCHAR(50) NULL,
    document_type NVARCHAR(10) NOT NULL CHECK (document_type IN ('pdf', 'image')),
    file_path NVARCHAR(500) NOT NULL,  -- 使用 NVARCHAR 支持中文路径
    file_name NVARCHAR(200) NOT NULL,
    file_size INT NOT NULL,
    mime_type NVARCHAR(100) NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
GO

-- 创建索引
CREATE INDEX IX_documents_title ON documents(title);
GO

-- 添加注释
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'文档表：存储文档和截图信息', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'documents';
GO

-- ============================================================
-- 7. 创建自动更新 updated_at 的触发器
-- ============================================================

-- projects 表触发器
IF OBJECT_ID('TR_projects_updated_at', 'TR') IS NOT NULL
    DROP TRIGGER TR_projects_updated_at;
GO

CREATE TRIGGER TR_projects_updated_at
ON projects
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE projects
    SET updated_at = GETDATE()
    FROM projects p
    INNER JOIN inserted i ON p.id = i.id;
END;
GO

-- interfaces 表触发器
IF OBJECT_ID('TR_interfaces_updated_at', 'TR') IS NOT NULL
    DROP TRIGGER TR_interfaces_updated_at;
GO

CREATE TRIGGER TR_interfaces_updated_at
ON interfaces
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE interfaces
    SET updated_at = GETDATE()
    FROM interfaces i
    INNER JOIN inserted ins ON i.id = ins.id;
END;
GO

-- dictionaries 表触发器
IF OBJECT_ID('TR_dictionaries_updated_at', 'TR') IS NOT NULL
    DROP TRIGGER TR_dictionaries_updated_at;
GO

CREATE TRIGGER TR_dictionaries_updated_at
ON dictionaries
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE dictionaries
    SET updated_at = GETDATE()
    FROM dictionaries d
    INNER JOIN inserted ins ON d.id = ins.id;
END;
GO

-- documents 表触发器
IF OBJECT_ID('TR_documents_updated_at', 'TR') IS NOT NULL
    DROP TRIGGER TR_documents_updated_at;
GO

CREATE TRIGGER TR_documents_updated_at
ON documents
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE documents
    SET updated_at = GETDATE()
    FROM documents d
    INNER JOIN inserted ins ON d.id = ins.id;
END;
GO

-- ============================================================
-- 8. 验证表创建
-- ============================================================
PRINT '========================================';
PRINT '数据库表创建完成！';
PRINT '========================================';
PRINT '';

SELECT 
    t.name AS TableName,
    COUNT(c.column_id) AS ColumnCount
FROM sys.tables t
INNER JOIN sys.columns c ON t.object_id = c.object_id
WHERE t.name IN ('projects', 'interfaces', 'parameters', 'dictionaries', 'dictionary_values', 'documents')
GROUP BY t.name
ORDER BY t.name;

PRINT '';
PRINT '所有表已成功创建！';
PRINT '注意：所有存储中文的字段已使用 NVARCHAR/NTEXT 类型，支持 Unicode 字符。';
GO

