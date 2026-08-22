#!/bin/bash
# 双击启动人才库智能体 Demo（macOS）
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "未检测到 Python3。"
    echo "macOS 请在终端执行：xcode-select --install 安装命令行工具后重试。"
    read -n 1 -s -r -p "按任意键退出..."
    exit 1
fi

if lsof -nP -iTCP:8080 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "端口 8080 已被占用。"
    echo "可以在 .env 里改 PORT 换端口，或先关闭占用 8080 的程序。"
    read -n 1 -s -r -p "按任意键退出..."
    exit 1
fi

echo "正在启动人才库智能体 Demo，浏览器将自动打开……"
echo "（停止服务：回到本窗口按 Ctrl+C）"
python3 server.py &
PID=$!
sleep 1.5
open "http://localhost:8080/"
wait $PID
