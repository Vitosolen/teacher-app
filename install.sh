#!/usr/bin/env bash
# 班级养宠物系统 · 一键安装（macOS / Linux）
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "============================================"
echo "  班级养宠物系统 - 一键安装"
echo "============================================"
echo

echo "[1/5] 检查 Python 环境 ..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "  [错误] 未检测到 python3，请先安装 Python 3.10+"
  echo "  Mac:  brew install python@3.11"
  echo "  Ubuntu: sudo apt install python3 python3-venv"
  exit 1
fi
python3 --version

echo
echo "[2/5] 检查 Node.js 环境 ..."
if ! command -v node >/dev/null 2>&1; then
  echo "  [错误] 未检测到 node，请先安装 Node.js 18+"
  echo "  下载：https://nodejs.org/"
  exit 1
fi
node --version

echo
echo "[3/5] 安装后端依赖 ..."
cd "$ROOT/class-pet-backend"
if [ ! -d .venv ]; then
  echo "  创建虚拟环境 .venv ..."
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
echo "  安装 Python 依赖（首次较慢）..."
pip install -r requirements.txt -q --disable-pip-version-check
if [ ! -f .env ]; then
  cp .env.example .env
  echo "  已生成 .env（可按需修改 JWT_SECRET）"
fi

echo
echo "[4/5] 初始化数据库（含预置物种 / 商品）..."
python init_db.py

echo
echo "[5/5] 安装前端依赖（约 200MB，首次较慢）..."
cd "$ROOT/class-pet-frontend"
if [ ! -d node_modules ]; then
  npm install
else
  echo "  node_modules 已存在，跳过"
fi

echo
echo "============================================"
echo "  安装完成！运行 ./start.sh 启动系统"
echo "============================================"
