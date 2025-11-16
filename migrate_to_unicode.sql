-- SQL Server 数据库迁移脚本：将 VARCHAR 字段改为 NVARCHAR 以支持中文
-- 执行此脚本前，请先备份数据库！

-- 注意：此脚本需要根据实际表结构调整
-- 如果表已存在数据，需要先迁移数据

USE HIS_Interface;
GO

-- 修改 projects 表
ALTER TABLE projects ALTER COLUMN name NVARCHAR(200) NOT NULL;
ALTER TABLE projects ALTER COLUMN manager NVARCHAR(100) NOT NULL;
ALTER TABLE projects ALTER COLUMN contact_info NTEXT NOT NULL;
ALTER TABLE projects ALTER COLUMN description NTEXT NULL;

-- 修改 interfaces 表
ALTER TABLE interfaces ALTER COLUMN name NVARCHAR(200) NOT NULL;
ALTER TABLE interfaces ALTER COLUMN description NTEXT NULL;
ALTER TABLE interfaces ALTER COLUMN category NVARCHAR(100) NULL;
ALTER TABLE interfaces ALTER COLUMN tags NVARCHAR(500) NULL;
ALTER TABLE interfaces ALTER COLUMN input_example NTEXT NULL;
ALTER TABLE interfaces ALTER COLUMN output_example NTEXT NULL;
ALTER TABLE interfaces ALTER COLUMN view_definition NTEXT NULL;
ALTER TABLE interfaces ALTER COLUMN notes NTEXT NULL;

-- 修改 parameters 表
ALTER TABLE parameters ALTER COLUMN name NVARCHAR(200) NOT NULL;
ALTER TABLE parameters ALTER COLUMN default_value NVARCHAR(500) NULL;
ALTER TABLE parameters ALTER COLUMN description NTEXT NULL;
ALTER TABLE parameters ALTER COLUMN example NVARCHAR(500) NULL;

-- 修改 dictionaries 表
ALTER TABLE dictionaries ALTER COLUMN name NVARCHAR(200) NOT NULL;
ALTER TABLE dictionaries ALTER COLUMN description NTEXT NULL;

-- 修改 dictionary_values 表
ALTER TABLE dictionary_values ALTER COLUMN value NVARCHAR(500) NOT NULL;
ALTER TABLE dictionary_values ALTER COLUMN description NTEXT NULL;

-- 修改 documents 表（如果存在）
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'documents')
BEGIN
    ALTER TABLE documents ALTER COLUMN title NVARCHAR(200) NOT NULL;
    ALTER TABLE documents ALTER COLUMN description NTEXT NULL;
    ALTER TABLE documents ALTER COLUMN region NVARCHAR(50) NULL;
    ALTER TABLE documents ALTER COLUMN person NVARCHAR(50) NULL;
    ALTER TABLE documents ALTER COLUMN file_name NVARCHAR(200) NOT NULL;
END
GO

PRINT '数据库字段类型迁移完成！';
PRINT '所有存储中文的字段已改为 NVARCHAR/NTEXT 类型。';

