@echo off
chcp 65001 >nul
echo ====================================
echo 正在停止并删除旧的 Docker 容器...
echo ====================================
docker stop my_order_app 2>nul
docker rm my_order_app 2>nul

echo ====================================
echo 正在检查并构建 Docker 镜像...
echo ====================================
docker build -t order-backend . 2>nul
if %errorlevel% neq 0 (
    echo 警告：镜像构建失败，将使用现有镜像启动...
)

echo ====================================
echo 正在启动新的 Docker 容器...
echo ====================================
docker run -d -p 7899:7899 --name my_order_app ^
  -v "%~dp0..\data":/app/data ^
  -v "%~dp0..\frontend":/app/frontend ^
  -v "%~dp0..\uploads":/app/uploads ^
  -v "%~dp0app.py":/app/app.py ^
  order-backend

if %errorlevel% equ 0 (
    echo ====================================
    echo 启动成功！请手动打开浏览器访问 http://localhost:7899
    echo ====================================
) else (
    echo ====================================
    echo 启动失败！请检查Docker是否正在运行
    echo ====================================
)

pause