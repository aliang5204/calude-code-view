@echo off
chcp 65001 >nul 2>&1
title AI Chat Web

echo ========================================
echo   AI Chat Web
echo ========================================
echo.

cd /d "%~dp0"

echo [Project Dir] %CD%
echo.

echo [1/2] Starting Backend on port 8176...
cd backend
start "AI-Backend" cmd /k python run.py
cd ..

echo Waiting for backend to start...
timeout /t 4 /nobreak >nul

echo [2/2] Starting Frontend on port 1420...
cd frontend
start "AI-Frontend" cmd /k npm run dev
cd ..

echo.
echo ========================================
echo   Backend  : http://localhost:8176
echo   Frontend : http://localhost:1420
echo ========================================
echo.
echo Opening browser in 2 seconds...

timeout /t 2 /nobreak >nul
start "" http://localhost:1420

pause
