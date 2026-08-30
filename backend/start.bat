@echo off
chcp 65001 >nul
echo ====================================
echo Stopping and removing old container...
echo ====================================
docker stop my_order_app 2>nul
docker rm my_order_app 2>nul

echo ====================================
echo Building Docker image...
echo ====================================
docker build -t order-backend e:\order_system\backend 2>nul
if %errorlevel% neq 0 (
    echo Warning: Build failed, using existing image...
)

echo ====================================
echo Starting new container...
echo ====================================
docker run -d -p 7899:7899 --name my_order_app -v e:\order_system\data:/app/data -v e:\order_system\frontend:/app/frontend -v e:\order_system\uploads:/app/uploads -v e:\order_system\backend:/app order-backend

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
