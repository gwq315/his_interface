-- 为 projects 表添加 attachments 字段（用于存储项目附件信息）
-- 执行时间：2024

-- 检查字段是否存在，如果不存在则添加
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('projects') 
    AND name = 'attachments'
)
BEGIN
    ALTER TABLE projects 
    ADD attachments NVARCHAR(MAX) NULL;
    
    PRINT '已添加 attachments 字段到 projects 表';
END
ELSE
BEGIN
    PRINT 'attachments 字段已存在，跳过添加';
END
GO

