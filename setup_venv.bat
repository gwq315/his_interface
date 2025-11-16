@echo off
chcp 65001 >nul
REM Create Python virtual environment script
REM Usage: Run setup_venv.bat in CMD

echo ========================================
echo   创建Python虚拟环境
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误- 未找到Python，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

python --version
echo.

REM Virtual environment directory name
set VENV_DIR=venv

REM Check if virtual environment already exists
if exist "%VENV_DIR%" (
    echo 虚拟环境已存在 - %VENV_DIR%
    echo 是否要重新创建(y/N)
    set /p RESPONSE=
    if /i "%RESPONSE%"=="y" (
        echo 删除现有虚拟环境...
        rmdir /s /q "%VENV_DIR%"
    ) else (
        echo 跳过创建虚拟环境
        pause
        exit /b 0
    )
)

REM Create virtual environment
echo 正在创建虚拟环境...
python -m venv %VENV_DIR%

if errorlevel 1 (
    echo 错误- 创建虚拟环境失败
    pause
    exit /b 1
)

REM Activate virtual environment and install dependencies
echo 激活虚拟环境...
call "%VENV_DIR%\Scripts\activate.bat"

REM Upgrade pip
echo 升级pip...
python -m pip install --upgrade pip

REM Install backend dependencies
echo 安装后端依赖...
cd backend

REM Set environment variables to prevent encoding issues
set PYTHONIOENCODING=utf-8
set PIP_NO_CACHE_DIR=1

REM Install dependencies with error handling
echo 正在安装Python依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo 错误- 依赖安装失败
    echo.
    echo 如果pyodbc安装失败，可能是Python 3.13兼容性问题
    echo 解决方案：
    echo 1. 尝试使用预编译的wheel文件
    echo 2. 或使用pymssql替代（修改requirements.txt，注释pyodbc，取消注释pymssql）
    echo 3. 或降级到Python 3.11或3.12
    echo.
    pause
    exit /b 1
)

cd ..

echo.
echo ========================================
echo   虚拟环境创建完成！
echo ========================================
echo.
echo 下次使用时，请先激活虚拟环境
echo   %VENV_DIR%\Scripts\activate.bat
echo.
echo 或者使用快速启动脚本
echo   start_backend.bat
echo   start_frontend.bat
echo.
pause






