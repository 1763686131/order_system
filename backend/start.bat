@echo off
chcp 65001 >nul

echo ====================================
echo 正在停止旧容器...
echo ====================================
docker stop my_order_app
docker rm my_order_app

echo.
echo ====================================
echo 正在启动新容器...
echo ====================================
docker run -d -p 7899:7899 --name my_order_app -v "e:/order_system/data":/app/data -v "e:/order_system/frontend":/app/frontend -v "e:/order_system/uploads":/app/uploads -v "e:/order_system/backend":/app order-backend

echo.
echo ====================================
echo 检查容器状态...
echo ====================================
docker ps | findstr my_order_app

echo.
echo ====================================
echo 显示最近日志...
echo ====================================
timeout /t 2 >nul
docker logs --tail 10 my_order_app

echo.
echo ====================================
echo 服务已启动，访问 http://localhost:7899
echo ====================================

pause
