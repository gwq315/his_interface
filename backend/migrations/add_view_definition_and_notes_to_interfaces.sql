-- 为 interfaces 表添加视图定义和备注说明字段
-- 执行时间: 2024

-- 添加视图定义字段（纯文本，用于存储数据库视图定义）
ALTER TABLE interfaces ADD COLUMN view_definition TEXT COMMENT '视图定义，存储数据库视图的SQL定义，纯文本格式';

-- 添加备注说明字段（HTML格式，用于存储富文本内容）
ALTER TABLE interfaces ADD COLUMN notes TEXT COMMENT '备注说明，支持HTML格式，用于存储常见操作说明、错误提示等图文内容';

