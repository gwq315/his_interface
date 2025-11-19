-- 为 documents 和 faqs 表添加 attachments 字段（用于存储多个附件信息）
-- 执行时间：2024

-- 为 documents 表添加 attachments 字段
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('documents') 
    AND name = 'attachments'
)
BEGIN
    ALTER TABLE documents 
    ADD attachments NVARCHAR(MAX) NULL;
    
    PRINT '已添加 attachments 字段到 documents 表';
END
ELSE
BEGIN
    PRINT 'attachments 字段已存在于 documents 表，跳过添加';
END
GO

-- 为 faqs 表添加 attachments 字段
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('faqs') 
    AND name = 'attachments'
)
BEGIN
    ALTER TABLE faqs 
    ADD attachments NVARCHAR(MAX) NULL;
    
    PRINT '已添加 attachments 字段到 faqs 表';
END
ELSE
BEGIN
    PRINT 'attachments 字段已存在于 faqs 表，跳过添加';
END
GO

