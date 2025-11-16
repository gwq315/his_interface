-- 数据库迁移脚本：添加project_id字段
-- 执行前请备份数据库！

-- ========== 1. 创建projects表（如果不存在） ==========
-- 注意：SQL Server中需要先创建projects表才能添加外键

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[projects]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[projects] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [name] NVARCHAR(200) NOT NULL,
        [manager] NVARCHAR(100) NOT NULL,
        [contact_info] NTEXT NOT NULL,
        [documents] NVARCHAR(MAX) NULL,
        [description] NTEXT NULL,
        [created_at] DATETIME2 DEFAULT GETDATE(),
        [updated_at] DATETIME2 DEFAULT GETDATE()
    )
    
    CREATE INDEX IX_projects_name ON [dbo].[projects]([name])
    
    PRINT 'Projects表创建成功'
END
ELSE
BEGIN
    PRINT 'Projects表已存在'
END
GO

-- ========== 2. 检查并添加interfaces表的project_id列 ==========

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[interfaces]') AND name = 'project_id')
BEGIN
    -- 先添加列（允许NULL，因为旧数据没有project_id）
    ALTER TABLE [dbo].[interfaces]
    ADD [project_id] INT NULL
    
    PRINT '已添加interfaces.project_id列'
END
ELSE
BEGIN
    PRINT 'interfaces.project_id列已存在'
END
GO

-- ========== 3. 检查并添加dictionaries表的project_id列 ==========

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[dictionaries]') AND name = 'project_id')
BEGIN
    -- 先添加列（允许NULL，因为旧数据没有project_id）
    ALTER TABLE [dbo].[dictionaries]
    ADD [project_id] INT NULL
    
    PRINT '已添加dictionaries.project_id列'
END
ELSE
BEGIN
    PRINT 'dictionaries.project_id列已存在'
END
GO

-- ========== 4. 添加外键约束（可选，如果已有数据需要先处理） ==========

-- 如果表中已有数据但没有project_id，需要先设置默认值或创建默认项目
-- 这里先不添加外键约束，让用户可以逐步迁移数据

-- 如果需要添加外键约束，取消下面的注释：
/*
-- 添加interfaces表的外键
IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_interfaces_project_id')
BEGIN
    ALTER TABLE [dbo].[interfaces]
    ADD CONSTRAINT FK_interfaces_project_id
    FOREIGN KEY ([project_id]) REFERENCES [dbo].[projects]([id])
    
    PRINT '已添加interfaces表的外键约束'
END

-- 添加dictionaries表的外键
IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_dictionaries_project_id')
BEGIN
    ALTER TABLE [dbo].[dictionaries]
    ADD CONSTRAINT FK_dictionaries_project_id
    FOREIGN KEY ([project_id]) REFERENCES [dbo].[projects]([id])
    
    PRINT '已添加dictionaries表的外键约束'
END
*/

-- ========== 5. 创建索引（提高查询性能） ==========

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_interfaces_project_id')
BEGIN
    CREATE INDEX IX_interfaces_project_id ON [dbo].[interfaces]([project_id])
    PRINT '已创建interfaces.project_id索引'
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_dictionaries_project_id')
BEGIN
    CREATE INDEX IX_dictionaries_project_id ON [dbo].[dictionaries]([project_id])
    PRINT '已创建dictionaries.project_id索引'
END
GO

PRINT '数据库迁移完成！'
PRINT '注意：如果interfaces和dictionaries表中有旧数据，需要手动设置project_id或创建默认项目'

