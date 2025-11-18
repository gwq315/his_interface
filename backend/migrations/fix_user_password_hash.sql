-- ============================================================
-- 修复用户密码（改为明文存储）
-- ============================================================
-- 如果数据库中已有用户但密码格式不正确，运行此脚本修复
-- ============================================================

-- 更新admin用户的密码（密码：admin123，明文存储）
UPDATE users
SET password_hash = N'admin123'
WHERE username = 'admin';
GO

-- 如果需要更新其他用户的密码，直接执行：
-- UPDATE users SET password_hash = N'新密码' WHERE username = '用户名';
-- 如果用户不需要密码，设置为NULL：
-- UPDATE users SET password_hash = NULL WHERE username = '用户名';
GO

PRINT N'用户密码修复完成！';
GO

