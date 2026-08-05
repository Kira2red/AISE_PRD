#!/bin/bash
# 手机监考 Demo 启动脚本
# 双击此文件即可在浏览器中预览

DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8081

# 杀掉旧进程
lsof -ti :$PORT | xargs kill -9 2>/dev/null

# 启动本地服务器
cd "$DIR"
/usr/bin/python3 -m http.server $PORT &
PID=$!
sleep 0.5

# 打开浏览器
open "http://localhost:$PORT/21_测评_设备调试.html"

echo "服务器已启动: http://localhost:$PORT"
echo "设备调试页: http://localhost:$PORT/21_测评_设备调试.html"
echo "手机引导页: http://localhost:$PORT/30_手机监考_引导页.html"
echo "手机直播页: http://localhost:$PORT/31_手机监考_直播页.html"
echo ""
echo "按 Ctrl+C 停止服务器"
wait $PID
