@echo off
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo 未检测到 Python。请先到 https://www.python.org 下载安装，
    echo 安装时勾选 "Add Python to PATH" 后重试。
    pause
    exit /b 1
)

echo 正在启动人才库智能体 Demo，浏览器将自动打开……
start "" http://localhost:8080
python server.py
pause
