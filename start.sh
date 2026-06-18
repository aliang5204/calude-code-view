#!/bin/bash
echo "========================================"
echo "  AI Chat Web - 个人专属对话助手"
echo "========================================"
echo ""

DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[1/2] 启动后端服务 (端口 8176)..."
cd "$DIR/backend" && python run.py &
BACKEND_PID=$!

sleep 2

echo "[2/2] 启动前端服务 (端口 1420)..."
cd "$DIR/frontend" && npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "  后端:  http://localhost:8176"
echo "  前端:  http://localhost:1420"
echo "========================================"
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
