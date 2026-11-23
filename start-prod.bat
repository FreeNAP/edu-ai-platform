@echo off
setlocal
cd /d %~dp0
echo [1/2] 构建前端...
cd frontend
call npm install
call npm run build
cd ..
echo [2/2] 启动后端（托管前端产物）...
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
endlocal
