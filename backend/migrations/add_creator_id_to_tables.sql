-- ============================================================
-- 为各个表添加创建人字段（creator_id）
-- ============================================================
-- 本脚本用于：
-- 1. 为interfaces表添加creator_id字段
-- 2. 为dictionaries表添加creator_id字段
-- 3. 为documents表添加creator_id字段
-- 4. 为faqs表添加creator_id字段
-- ============================================================

-- 1. 为interfaces表添加creator_id字段
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('interfaces') AND name = 'creator_id')
BEGIN
    ALTER TABLE interfaces
    ADD creator_id INT NULL;
    
    -- 创建外键约束
    ALTER TABLE interfaces
    ADD CONSTRAINT FK_interfaces_creator FOREIGN KEY (creator_id) 
        REFERENCES users(id) ON DELETE SET NULL;
    
    -- 创建索引
    CREATE INDEX IX_interfaces_creator_id ON interfaces(creator_id);
    
    PRINT N'已添加interfaces表的创建人字段';
END
ELSE
BEGIN
    PRINT N'interfaces表的创建人字段已存在';
END
GO

-- 2. 为dictionaries表添加creator_id字段
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dictionaries') AND name = 'creator_id')
BEGIN
    ALTER TABLE dictionaries
    ADD creator_id INT NULL;
    
    -- 创建外键约束
    ALTER TABLE dictionaries
    ADD CONSTRAINT FK_dictionaries_creator FOREIGN KEY (creator_id) 
        REFERENCES users(id) ON DELETE SET NULL;
    
    -- 创建索引
    CREATE INDEX IX_dictionaries_creator_id ON dictionaries(creator_id);
    
    PRINT N'已添加dictionaries表的创建人字段';
END
ELSE
BEGIN
    PRINT N'dictionaries表的创建人字段已存在';
END
GO

-- 3. 为documents表添加creator_id字段
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('documents') AND name = 'creator_id')
BEGIN
    ALTER TABLE documents
    ADD creator_id INT NULL;
    
    -- 创建外键约束
    ALTER TABLE documents
    ADD CONSTRAINT FK_documents_creator FOREIGN KEY (creator_id) 
        REFERENCES users(id) ON DELETE SET NULL;
    
    -- 创建索引
    CREATE INDEX IX_documents_creator_id ON documents(creator_id);
    
    PRINT N'已添加documents表的创建人字段';
END
ELSE
BEGIN
    PRINT N'documents表的创建人字段已存在';
END
GO

-- 4. 为faqs表添加creator_id字段
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('faqs') AND name = 'creator_id')
BEGIN
    ALTER TABLE faqs
    ADD creator_id INT NULL;
    
    -- 创建外键约束
    ALTER TABLE faqs
    ADD CONSTRAINT FK_faqs_creator FOREIGN KEY (creator_id) 
        REFERENCES users(id) ON DELETE SET NULL;
    
    -- 创建索引
    CREATE INDEX IX_faqs_creator_id ON faqs(creator_id);
    
    PRINT N'已添加faqs表的创建人字段';
END
ELSE
BEGIN
    PRINT N'faqs表的创建人字段已存在';
END
GO

PRINT N'所有表的创建人字段添加完成！';
GO

