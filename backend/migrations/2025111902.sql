-- 为 faqs 表添加 content_type 和 rich_content 字段
-- content_type: 内容类型，'attachment'（附件类型）或 'rich_text'（富文本类型）
-- rich_content: 富文本内容，存储HTML格式的图文混排内容

-- 添加 content_type 字段
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('faqs') 
    AND name = 'content_type'
)
BEGIN
    ALTER TABLE faqs 
    ADD content_type NVARCHAR(20) NULL DEFAULT 'attachment';
    PRINT '已添加 content_type 字段到 faqs 表';
END
ELSE
BEGIN
    PRINT 'faqs 表已存在 content_type 字段，跳过添加';
END
GO

-- 添加 rich_content 字段
IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('faqs') 
    AND name = 'rich_content'
)
BEGIN
    ALTER TABLE faqs 
    ADD rich_content NVARCHAR(MAX) NULL;
    PRINT '已添加 rich_content 字段到 faqs 表';
END
ELSE
BEGIN
    PRINT 'faqs 表已存在 rich_content 字段，跳过添加';
END
GO

-- 更新现有数据：将所有现有数据设置为 attachment 类型
UPDATE faqs 
SET content_type = 'attachment' 
WHERE content_type IS NULL;
GO

PRINT '数据库迁移完成：已为 faqs 表添加 content_type 和 rich_content 字段';

