@echo off
chcp 65001 >nul
title 班级养宠物系统 · 一键安装

echo ============================================
echo   班级养宠物系统 - 一键安装
echo ============================================
echo.

echo [1/5] 检查 Python 环境 ...
where python >nul 2>nul
if errorlevel 1 (
  echo   [错误] 未检测到 Python，请先安装 Python 3.10+
  echo   下载：https://www.python.org/downloads/
  echo   安装时勾选 "Add Python to PATH"
  pause
  exit /b 1
)
python --version

echo.
echo [2/5] 检查 Node.js 环境 ...
where node >nul 2>nul
if errorlevel 1 (
  echo   [错误] 未检测到 Node.js，请先安装 Node.js 18+
  echo   下载：https://nodejs.org/
  pause
  exit /b 1
)
node --version

echo.
echo [3/5] 安装后端依赖 ...
cd /d "%~dp0class-pet-backend"
if not exist .venv (
  echo   创建虚拟环境 .venv ...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
echo   安装 Python 依赖（首次较慢）...
pip install -r requirements.txt -q --disable-pip-version-check
if not exist .env (
  copy .env.example .env >nul
  echo   已生成 .env（可按需修改 JWT_SECRET）
)

echo.
echo [4/5] 初始化数据库（含预置物种 / 商品）...
python init_db.py

echo.
echo [5/5] 安装前端依赖（约 200MB，首次较慢）...
cd /d "%~dp0class-pet-frontend"
if not exist .env.example (
  echo VITE_BACKEND_PORT=8000 > .env.example
)
if not exist node_modules (
  call npm install
) else (
  echo   node_modules 已存在，跳过
)

echo.
echo ============================================
echo   安装完成！双击 start.bat 启动系统
echo ============================================
echo.
pause
