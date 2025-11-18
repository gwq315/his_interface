-- 创建常见问题表 (faqs)
-- 用于存储常见问题信息，类似documents表，但使用module字段替代region字段

IF OBJECT_ID('faqs', 'U') IS NOT NULL
    DROP TABLE faqs;
GO

CREATE TABLE faqs (
    id INT IDENTITY(1,1) PRIMARY KEY,
    title NVARCHAR(200) NOT NULL,
    description NTEXT NULL,
    module NVARCHAR(50) NULL,
    person NVARCHAR(50) NULL,
    document_type NVARCHAR(20) NOT NULL CHECK (document_type IN ('pdf', 'image')),
    file_path NVARCHAR(500) NOT NULL,
    file_name NVARCHAR(200) NOT NULL,
    file_size INT NOT NULL,
    mime_type NVARCHAR(100) NULL,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
GO

-- 创建索引
CREATE INDEX IX_faqs_title ON faqs(title);
GO

-- 添加注释
EXEC sp_addextendedproperty 
    @name = N'MS_Description', 
    @value = N'常见问题表：存储常见问题信息，用于集中保存和管理', 
    @level0type = N'SCHEMA', @level0name = N'dbo', 
    @level1type = N'TABLE', @level1name = N'faqs';
GO

