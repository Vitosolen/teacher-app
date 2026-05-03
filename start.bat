@echo off
chcp 65001 >nul
title 班级养宠物系统 · 一键启动

echo.
echo ============================================
echo   班级养宠物系统 - 一键启动
echo ============================================
echo.

REM 检查依赖
if not exist "%~dp0class-pet-backend\.venv" (
  echo [错误] 依赖未安装，请先双击 install.bat
  pause
  exit /b 1
)
if not exist "%~dp0class-pet-frontend\node_modules" (
  echo [错误] 依赖未安装，请先双击 install.bat
  pause
  exit /b 1
)

REM 自清理：先杀掉占用 8000 / 5173 / 5174 / 5175 的旧进程
echo [1/4] 清理旧进程 ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr LISTENING') do (
  taskkill /F /PID %%a >nul 2>&1
)
for %%p in (5173 5174 5175) do (
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%p " ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
  )
)
timeout /t 1 /nobreak >nul

echo [2/4] 启动后端（端口 8000）...
start "class-pet-backend [8000]" cmd /k "cd /d %~dp0class-pet-backend && .venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

echo [3/4] 启动前端（端口 5173）...
start "class-pet-frontend [5173]" cmd /k "cd /d %~dp0class-pet-frontend && npm run dev"

echo [4/4] 等待服务就绪（10 秒）...
timeout /t 10 /nobreak >nul

start http://127.0.0.1:5173

echo.
echo ============================================
echo   启动完成！
echo   后端窗口: class-pet-backend [8000]
echo   前端窗口: class-pet-frontend [5173]
echo   关闭那两个 cmd 窗口即可停止服务
echo ============================================
echo.
timeout /t 5 /nobreak >nul
exit
