@echo off
chcp 65001 >nul
REM 数据库迁移脚本：添加project_id字段
REM Usage: Run migrate_db.bat in CMD

echo ========================================
echo   数据库迁移：添加project_id字段
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo 错误- 虚拟环境不存在！
    echo 请先运行 setup_venv.bat 创建虚拟环境
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Set environment variables
set PYTHONIOENCODING=utf-8

echo 正在执行数据库迁移...
echo.

cd backend
python migrations\add_project_id.py

echo.
echo 迁移完成！
echo.
pause

