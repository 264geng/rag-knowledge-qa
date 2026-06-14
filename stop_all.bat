@echo off
chcp 65001 >nul 2>nul
title RAG Stop All

echo ========================================
echo   Stopping all RAG services...
echo ========================================
echo.

echo [1] Killing processes on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING" 2^>nul') do (
    echo   Killing PID: %%a
    taskkill /PID %%a /F >nul 2>nul
)

echo [2] Killing processes on port 5173...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING" 2^>nul') do (
    echo   Killing PID: %%a
    taskkill /PID %%a /F >nul 2>nul
)

echo [3] Killing RAG window processes...
taskkill /FI "WINDOWTITLE eq RAG-Backend*" /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq RAG-Frontend*" /F >nul 2>nul

timeout /t 2 /nobreak >nul

echo.
echo   All services stopped.
echo.
pause
