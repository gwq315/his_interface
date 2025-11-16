@echo off
chcp 65001 >nul
REM Activate virtual environment script
REM Usage: Run activate_venv.bat in CMD

set VENV_DIR=venv
set VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat

if exist "%VENV_ACTIVATE%" (
    echo 激活虚拟环境...
    call "%VENV_ACTIVATE%"
    echo 虚拟环境已激活！
    echo.
    where python
) else (
    echo 错误- 虚拟环境不存在！
    echo 请先运行 setup_venv.bat 创建虚拟环境
)




