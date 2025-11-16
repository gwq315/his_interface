-- 为 interfaces 表添加 input_example 和 output_example 字段
-- 执行时间：2024

-- 检查字段是否存在，如果不存在则添加
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('interfaces') 
    AND name = 'input_example'
)
BEGIN
    ALTER TABLE interfaces 
    ADD input_example NVARCHAR(MAX) NULL;
    
    PRINT '已添加 input_example 字段到 interfaces 表';
END
ELSE
BEGIN
    PRINT 'input_example 字段已存在，跳过添加';
END
GO

IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('interfaces') 
    AND name = 'output_example'
)
BEGIN
    ALTER TABLE interfaces 
    ADD output_example NVARCHAR(MAX) NULL;
    
    PRINT '已添加 output_example 字段到 interfaces 表';
END
ELSE
BEGIN
    PRINT 'output_example 字段已存在，跳过添加';
END
GO

