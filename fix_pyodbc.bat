@echo off
chcp 65001 >nul
REM 修复pyodbc安装问题的辅助脚本
REM Usage: Run fix_pyodbc.bat in CMD

echo ========================================
echo   修复pyodbc安装问题
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
set PIP_NO_CACHE_DIR=1

echo 当前Python版本:
python --version
echo.

echo 方案1: 尝试使用预编译wheel文件安装pyodbc
echo 如果失败，将尝试其他方案
echo.
pip install pyodbc --only-binary :all:
if errorlevel 1 (
    echo.
    echo 方案1失败，尝试方案2: 使用最新版本
    pip install --upgrade pip
    pip install pyodbc --upgrade
    if errorlevel 1 (
        echo.
        echo 方案2也失败，建议使用pymssql作为替代
        echo.
        echo 请手动修改 backend\requirements.txt:
        echo 1. 注释掉 pyodbc 行（在前面添加 #）
        echo 2. 取消注释 pymssql 行（删除前面的 #）
        echo 3. 然后运行: pip install -r backend\requirements.txt
        echo.
        echo 详细说明请查看: backend\PYODBC_INSTALL.md
        pause
        exit /b 1
    )
)

echo.
echo pyodbc安装成功！
echo.
python -c "import pyodbc; print('pyodbc版本:', pyodbc.version)"
echo.
pause

