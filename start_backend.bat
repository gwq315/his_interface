@echo off
chcp 65001 >nul
REM Start backend service script
REM Usage: Run start_backend.bat in CMD

echo ========================================
echo   启动后端服务
echo ========================================
echo.

REM Virtual environment directory
set VENV_DIR=venv
set VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat

REM Check if virtual environment exists
if not exist "%VENV_ACTIVATE%" (
    echo 错误- 虚拟环境不存在！
    echo 请先运行 setup_venv.bat 创建虚拟环境
    pause
    exit /b 1
)

REM Activate virtual environment
call "%VENV_ACTIVATE%"

REM Check if backend directory exists
if not exist "backend" (
    echo 错误- 找不到backend目录
    pause
    exit /b 1
)

REM Check if config file exists
if not exist "backend\config.ini" (
    echo 警告- 找不到backend\config.ini配置文件
    echo 请先复制 config.ini.example 为 config.ini 并配置数据库连接
    echo.
)

REM Switch to project root directory
cd /d %~dp0

echo 启动后端服务...
echo 服务地址 - http://localhost:8000
echo API文档 - http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.

REM Start service from project root directory
REM 必须在项目根目录运行，才能正确导入backend模块
python -m uvicorn backend.app.main:app --reload --port 8000

pause




