@echo off
chcp 65001 >nul
REM 重启后端服务脚本
REM Usage: Run restart_backend.bat in CMD

echo ========================================
echo   重启后端服务
echo ========================================
echo.

REM 查找并结束占用8000端口的进程
echo 正在查找占用8000端口的进程...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo 发现进程 PID: %%a
    taskkill /F /PID %%a >nul 2>&1
    if %errorlevel% equ 0 (
        echo 已结束进程 PID: %%a
    ) else (
        echo 无法结束进程 PID: %%a，可能需要管理员权限
    )
)

timeout /t 2 /nobreak >nul

echo.
echo 正在启动后端服务...
echo.

call start_backend.bat

