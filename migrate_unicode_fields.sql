-- ============================================================
-- Unicode 字段迁移脚本
-- 将可能包含中文的字段从 VARCHAR 改为 NVARCHAR
-- ============================================================
-- 说明：
-- 此脚本用于更新现有数据库，将以下字段改为 NVARCHAR 类型：
-- 1. interfaces.code
-- 2. interfaces.url
-- 3. dictionaries.code
-- 4. documents.file_path
-- ============================================================

USE HIS_Interface;
GO

PRINT '开始迁移 Unicode 字段...';
PRINT '';

-- ============================================================
-- 1. 修改 interfaces 表
-- ============================================================
PRINT '修改 interfaces 表...';

-- 修改 code 字段
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('interfaces') AND name = 'code' AND system_type_id = 167)  -- 167 = VARCHAR
BEGIN
    ALTER TABLE interfaces ALTER COLUMN code NVARCHAR(100) NOT NULL;
    PRINT '  ✓ interfaces.code 已改为 NVARCHAR(100)';
END
ELSE
BEGIN
    PRINT '  - interfaces.code 已经是 NVARCHAR 类型或不存在';
END

-- 修改 url 字段
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('interfaces') AND name = 'url' AND system_type_id = 167)  -- 167 = VARCHAR
BEGIN
    ALTER TABLE interfaces ALTER COLUMN url NVARCHAR(500) NULL;
    PRINT '  ✓ interfaces.url 已改为 NVARCHAR(500)';
END
ELSE
BEGIN
    PRINT '  - interfaces.url 已经是 NVARCHAR 类型或不存在';
END

GO

-- ============================================================
-- 2. 修改 dictionaries 表
-- ============================================================
PRINT '修改 dictionaries 表...';

-- 修改 code 字段
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dictionaries') AND name = 'code' AND system_type_id = 167)  -- 167 = VARCHAR
BEGIN
    ALTER TABLE dictionaries ALTER COLUMN code NVARCHAR(100) NOT NULL;
    PRINT '  ✓ dictionaries.code 已改为 NVARCHAR(100)';
END
ELSE
BEGIN
    PRINT '  - dictionaries.code 已经是 NVARCHAR 类型或不存在';
END

GO

-- ============================================================
-- 3. 修改 documents 表
-- ============================================================
PRINT '修改 documents 表...';

-- 修改 file_path 字段
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('documents') AND name = 'file_path' AND system_type_id = 167)  -- 167 = VARCHAR
BEGIN
    ALTER TABLE documents ALTER COLUMN file_path NVARCHAR(500) NOT NULL;
    PRINT '  ✓ documents.file_path 已改为 NVARCHAR(500)';
END
ELSE
BEGIN
    PRINT '  - documents.file_path 已经是 NVARCHAR 类型或不存在';
END

GO

PRINT '';
PRINT '========================================';
PRINT 'Unicode 字段迁移完成！';
PRINT '========================================';
PRINT '';
PRINT '所有可能包含中文的字段已改为 NVARCHAR 类型。';
PRINT '注意：如果表中已有乱码数据，需要重新录入。';
GO

