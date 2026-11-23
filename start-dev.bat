@echo off
setlocal
cd /d %~dp0
start "edu-backend" cmd /k "cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
timeout /t 3 >nul
start "edu-frontend" cmd /k "cd frontend && npm run dev"
echo.
echo 后端: http://127.0.0.1:8000  (API 文档 /docs)
echo 前端: http://localhost:5173
endlocal
