@echo off
chcp 65001 >nul
REM Start frontend service script
REM Usage: Run start_frontend.bat in CMD

echo ========================================
echo   启动前端服务
echo ========================================
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误- 未找到Node.js，请先安装Node.js 16或更高版本
    pause
    exit /b 1
)

node --version
echo.

REM Check if frontend directory exists
if not exist "frontend" (
    echo 错误- 找不到frontend目录
    pause
    exit /b 1
)

REM Switch to project root directory
cd /d %~dp0

REM Check if node_modules exists
if not exist "frontend\node_modules" (
    echo 检测到node_modules不存在，正在安装依赖...
    cd frontend
    call npm install
    cd ..
    echo.
)

echo 启动前端服务...
echo 服务地址 - http://localhost:5173
echo.
echo 按 Ctrl+C 停止服务
echo.

REM Start service
cd frontend
call npm run dev

pause




