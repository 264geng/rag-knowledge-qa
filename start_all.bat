@echo off
chcp 65001 >nul 2>nul
title RAG Knowledge QA

echo ========================================
echo   RAG Knowledge QA - Starting...
echo ========================================
echo.

echo [1] Killing old processes on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING" 2^>nul') do (
    echo   Killing PID: %%a
    taskkill /PID %%a /F >nul 2>nul
)

echo [2] Killing old processes on port 5173...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING" 2^>nul') do (
    echo   Killing PID: %%a
    taskkill /PID %%a /F >nul 2>nul
)

taskkill /FI "WINDOWTITLE eq RAG-Backend*" /F >nul 2>nul
taskkill /FI "WINDOWTITLE eq RAG-Frontend*" /F >nul 2>nul

timeout /t 2 /nobreak >nul
echo   Old processes cleaned.
echo.

echo [3] Starting backend on port 8000...
cd /d "%~dp0backend"
start "RAG-Backend" cmd /k "title RAG-Backend && venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo   Backend: http://localhost:8000
echo.

timeout /t 5 /nobreak >nul

echo [4] Starting frontend on port 5173...
cd /d "%~dp0frontend"
start "RAG-Frontend" cmd /k "title RAG-Frontend && npm run dev"
echo   Frontend: http://localhost:5173
echo.

echo ========================================
echo   All services started!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   Admin:    admin / admin123
echo ========================================
echo.
pause
