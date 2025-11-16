-- 创建文档/截图表
-- 用于集中保存和管理文档（PDF）和截图（图片）

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[documents]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[documents] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [title] NVARCHAR(200) NOT NULL,
        [description] NTEXT NULL,
        [region] NVARCHAR(50) NULL,
        [person] NVARCHAR(50) NULL,
        [document_type] NVARCHAR(20) NOT NULL,
        [file_path] NVARCHAR(500) NOT NULL,
        [file_name] NVARCHAR(200) NOT NULL,
        [file_size] INT NOT NULL,
        [mime_type] NVARCHAR(100) NULL,
        [created_at] DATETIME NOT NULL DEFAULT GETDATE(),
        [updated_at] DATETIME NOT NULL DEFAULT GETDATE()
    );
    
    -- 创建索引
    CREATE INDEX [IX_documents_title] ON [dbo].[documents] ([title]);
    CREATE INDEX [IX_documents_document_type] ON [dbo].[documents] ([document_type]);
    CREATE INDEX [IX_documents_created_at] ON [dbo].[documents] ([created_at]);
    
    PRINT '文档表创建成功';
END
ELSE
BEGIN
    PRINT '文档表已存在';
END
GO

