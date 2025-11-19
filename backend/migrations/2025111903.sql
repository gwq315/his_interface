-- 修改 faqs 表的文件相关字段，使其允许 NULL（支持富文本类型）
-- 富文本类型的常见问题不需要文件，因此这些字段应该允许 NULL

-- 修改 file_path 字段为允许 NULL
IF EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('faqs') 
    AND name = 'file_path'
    AND is_nullable = 0
)
BEGIN
    ALTER TABLE faqs 
    ALTER COLUMN file_path NVARCHAR(500) NULL;
    PRINT '已修改 file_path 字段为允许 NULL';
END
ELSE
BEGIN
    PRINT 'file_path 字段已允许 NULL 或不存在，跳过修改';
END
GO

-- 修改 file_name 字段为允许 NULL
IF EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('faqs') 
    AND name = 'file_name'
    AND is_nullable = 0
)
BEGIN
    ALTER TABLE faqs 
    ALTER COLUMN file_name NVARCHAR(200) NULL;
    PRINT '已修改 file_name 字段为允许 NULL';
END
ELSE
BEGIN
    PRINT 'file_name 字段已允许 NULL 或不存在，跳过修改';
END
GO

-- 修改 file_size 字段为允许 NULL
IF EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('faqs') 
    AND name = 'file_size'
    AND is_nullable = 0
)
BEGIN
    ALTER TABLE faqs 
    ALTER COLUMN file_size INT NULL;
    PRINT '已修改 file_size 字段为允许 NULL';
END
ELSE
BEGIN
    PRINT 'file_size 字段已允许 NULL 或不存在，跳过修改';
END
GO

PRINT '数据库迁移完成：已修改 faqs 表的文件相关字段为允许 NULL';

