@echo off
chcp 65001 >nul

REM 自动获取当前脚本所在目录的父目录（项目根目录）
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

echo ====================================
echo Project Root: %PROJECT_ROOT%
echo ====================================

echo ====================================
echo Stopping and removing old container...
echo ====================================
docker stop my_order_app 2>nul
docker rm my_order_app 2>nul

echo ====================================
echo Building Docker image...
echo ====================================
docker build -t order-backend "%PROJECT_ROOT%\backend" 2>nul
if %errorlevel% neq 0 (
    echo Warning: Build failed, using existing image...
)

echo ====================================
echo Starting new container...
echo ====================================
docker run -d -p 7899:7899 --name my_order_app -e PYTHONDONTWRITEBYTECODE=1 -v "%PROJECT_ROOT%\data":/app/data -v "%PROJECT_ROOT%\frontend":/app/frontend -v "%PROJECT_ROOT%\uploads":/app/uploads -v "%PROJECT_ROOT%\backend":/app order-backend

if %errorlevel% equ 0 (
    echo ====================================
    echo Success! Visit http://localhost:7899
    echo ====================================
    timeout /t 2 >nul
    docker logs --tail 10 my_order_app
) else (
    echo ====================================
    echo Failed! Please check if Docker is running
    echo ====================================
)

pause
