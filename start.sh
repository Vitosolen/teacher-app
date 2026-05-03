#!/usr/bin/env bash
# 班级养宠物系统 · 一键启动（macOS / Linux）
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

# 检查依赖
if [ ! -d "$ROOT/class-pet-backend/.venv" ] || [ ! -d "$ROOT/class-pet-frontend/node_modules" ]; then
  echo "依赖未安装，先运行 ./install.sh"
  exit 1
fi

echo "============================================"
echo "  班级养宠物系统 - 启动中"
echo "============================================"
echo

# 后端默认端口
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

# 启动后端
echo "[1/2] 启动后端 (port $BACKEND_PORT) ..."
(
  cd "$ROOT/class-pet-backend"
  # shellcheck disable=SC1091
  source .venv/bin/activate
  exec uvicorn app.main:app --host 127.0.0.1 --port "$BACKEND_PORT"
) &
BACKEND_PID=$!

# 启动前端
echo "[2/2] 启动前端 (port $FRONTEND_PORT) ..."
(
  cd "$ROOT/class-pet-frontend"
  exec npm run dev -- --port "$FRONTEND_PORT"
) &
FRONTEND_PID=$!

# Ctrl+C 同时关掉两个
trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT TERM

echo
echo "============================================"
echo "  启动完成！打开浏览器访问："
echo "  http://127.0.0.1:$FRONTEND_PORT"
echo "  按 Ctrl+C 停止"
echo "============================================"
echo

wait
