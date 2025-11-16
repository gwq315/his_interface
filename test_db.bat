@echo off
chcp 65001 >nul
REM 测试数据库连接脚本
REM Usage: Run test_db.bat in CMD

echo ========================================
echo   测试数据库连接
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

REM Switch to project root directory
cd /d %~dp0

echo 正在测试数据库连接...
echo.

python -c "from backend.database import engine; conn = engine.connect(); print('数据库连接成功！'); conn.close()"

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   数据库连接测试通过！
    echo ========================================
) else (
    echo.
    echo ========================================
    echo   数据库连接失败！
    echo   请检查：
    echo   1. SQL Server服务是否启动
    echo   2. backend\config.ini 配置是否正确
    echo   3. ODBC驱动是否已安装
    echo ========================================
)

echo.
pause

