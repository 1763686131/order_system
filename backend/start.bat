@echo off
setlocal
chcp 65001 >nul

pushd "%~dp0.." || (
    echo Failed to locate project root.
    pause
    exit /b 1
)
set "PROJECT_ROOT=%CD%"
popd

echo ====================================
echo Project Root: %PROJECT_ROOT%
echo ====================================

docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not available. Please make sure Docker Desktop is running
    echo and this terminal has permission to access Docker.
    pause
    exit /b 1
)

echo ====================================
echo Stopping and removing old container...
echo ====================================
docker stop my_order_app >nul 2>&1
docker rm my_order_app >nul 2>&1

echo ====================================
echo Building Docker image...
echo ====================================
docker build -t order-backend "%PROJECT_ROOT%\backend"
if %errorlevel% neq 0 (
    echo ====================================
    echo Build failed. See the Docker error above.
    echo If the error mentions python:3.10-slim or auth.docker.io,
    echo pull the base image first after fixing Docker Hub access:
    echo docker pull python:3.10-slim
    echo ====================================
    pause
    exit /b 1
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
    echo Failed to start the container. See the Docker error above.
    echo ====================================
)

pause
