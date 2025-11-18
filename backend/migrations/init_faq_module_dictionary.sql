-- ============================================================
-- 初始化常见问题模块字典
-- ============================================================
-- 本脚本用于创建常见问题模块字典，包含预定义的模块选项
-- 字典编码: FAQ_MODULE
-- ============================================================

-- 1. 检查并创建默认项目（如果不存在）
-- 注意：这里假设至少有一个项目存在，如果没有项目，请先创建一个项目
-- 或者修改下面的 project_id 为实际存在的项目ID

DECLARE @project_id INT;
DECLARE @dictionary_id INT;

-- 获取第一个项目ID，如果没有项目则创建一个默认项目
SELECT TOP 1 @project_id = id FROM projects ORDER BY id;

IF @project_id IS NULL
BEGIN
    -- 如果没有项目，创建一个默认项目
    INSERT INTO projects (name, manager, contact_info, description)
    VALUES (N'系统默认项目', N'系统管理员', N'系统', N'系统默认项目，用于存储系统级字典');
    
    SET @project_id = SCOPE_IDENTITY();
    PRINT N'已创建默认项目，ID: ' + CAST(@project_id AS NVARCHAR(10));
END
ELSE
BEGIN
    PRINT N'使用现有项目，ID: ' + CAST(@project_id AS NVARCHAR(10));
END

-- 2. 检查字典是否已存在
IF EXISTS (SELECT 1 FROM dictionaries WHERE code = N'FAQ_MODULE')
BEGIN
    PRINT N'字典 FAQ_MODULE 已存在，跳过创建';
    SELECT @dictionary_id = id FROM dictionaries WHERE code = N'FAQ_MODULE';
END
ELSE
BEGIN
    -- 3. 创建常见问题模块字典
    INSERT INTO dictionaries (project_id, name, code, description)
    VALUES (
        @project_id,
        N'常见问题模块',
        N'FAQ_MODULE',
        N'常见问题所属模块字典，用于分类管理常见问题'
    );
    
    SET @dictionary_id = SCOPE_IDENTITY();
    PRINT N'已创建字典 FAQ_MODULE，ID: ' + CAST(@dictionary_id AS NVARCHAR(10));
END

-- 4. 清空现有字典值（如果字典已存在，重新初始化）
DELETE FROM dictionary_values WHERE dictionary_id = @dictionary_id;

-- 5. 插入预定义的模块字典值
-- 编号、名称、类别、添加日期 对应的字典值
INSERT INTO dictionary_values (dictionary_id, [key], value, description, order_index)
VALUES
    (@dictionary_id, N'1', N'患者管理', N'患者相关常见问题模块', 1),
    (@dictionary_id, N'2', N'医嘱管理', N'医嘱相关常见问题模块', 2),
    (@dictionary_id, N'3', N'收费管理', N'收费相关常见问题模块', 3),
    (@dictionary_id, N'4', N'药品管理', N'药品相关常见问题模块', 4),
    (@dictionary_id, N'5', N'检验检查', N'检验检查相关常见问题模块', 5),
    (@dictionary_id, N'6', N'系统设置', N'系统设置相关常见问题模块', 6),
    (@dictionary_id, N'7', N'报表统计', N'报表统计相关常见问题模块', 7),
    (@dictionary_id, N'8', N'其他', N'其他类别常见问题模块', 8);

PRINT N'已创建 ' + CAST(@@ROWCOUNT AS NVARCHAR(10)) + N' 个字典值';

-- 6. 显示创建的字典信息
SELECT 
    d.id AS 编号,
    d.name AS 名称,
    d.code AS 编码,
    d.description AS 类别,
    d.created_at AS 添加日期,
    COUNT(dv.id) AS 字典值数量
FROM dictionaries d
LEFT JOIN dictionary_values dv ON d.id = dv.dictionary_id
WHERE d.code = N'FAQ_MODULE'
GROUP BY d.id, d.name, d.code, d.description, d.created_at;

-- 7. 显示字典值列表
SELECT 
    dv.id AS 编号,
    dv.[key] AS 键,
    dv.value AS 名称,
    dv.description AS 类别,
    dv.order_index AS 排序,
    dv.created_at AS 添加日期
FROM dictionary_values dv
INNER JOIN dictionaries d ON dv.dictionary_id = d.id
WHERE d.code = N'FAQ_MODULE'
ORDER BY dv.order_index, dv.id;

PRINT N'常见问题模块字典初始化完成！';
GO

