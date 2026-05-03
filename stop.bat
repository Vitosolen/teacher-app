@echo off
chcp 65001 >nul
title 班级养宠物系统 · 停止

echo.
echo ============================================
echo   班级养宠物系统 - 停止服务
echo ============================================
echo.

REM 停止后端（8002）
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8002 " ^| findstr LISTENING') do (
  echo 停止后端 PID %%a
  taskkill /F /PID %%a >nul 2>&1
)

REM 停止前端（5173 / 5174 / 5175）
for %%p in (5173 5174 5175) do (
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%p " ^| findstr LISTENING') do (
    echo 停止前端 PID %%a [端口 %%p]
    taskkill /F /PID %%a >nul 2>&1
  )
)

echo.
echo === 已停止 ===
echo.
timeout /t 2 /nobreak >nul
exit
