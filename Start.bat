@echo off
chcp 65001 >nul
title 抖音热搜监控 - 启动中...

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║    🔥  抖音热搜监控系统  🔥              ║
echo  ║        正在准备环境，请稍候...            ║
echo  ╚══════════════════════════════════════════╝
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python！
    echo.
    echo 请先安装 Python：
    echo   1. 访问 https://www.python.org/downloads/
    echo   2. 下载并安装 Python 3.8 或更高版本
    echo   3. 安装时勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [1/3] 检测到 Python ✓

:: 检查/创建虚拟环境
if not exist "venv" (
    echo [2/3] 首次运行，正在创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败！
        pause
        exit /b 1
    )
    echo      虚拟环境创建成功 ✓
    
    echo [2/3] 正在安装依赖包（可能需要几分钟）...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt -q
    if errorlevel 1 (
        echo [错误] 安装依赖失败！
        pause
        exit /b 1
    )
    echo      依赖安装完成 ✓
) else (
    echo [2/3] 虚拟环境已存在 ✓
    call venv\Scripts\activate.bat
)

echo [3/3] 正在启动服务...
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║  服务已启动！                              ║
echo  ║                                            ║
echo  ║  请在浏览器打开:  http://localhost:5001    ║
echo  ║                                            ║
echo  ║  按 Ctrl+C 可停止服务                      ║
echo  ╚══════════════════════════════════════════╝
echo.

:: 自动打开浏览器
start http://localhost:5001

:: 启动服务
python run.py
