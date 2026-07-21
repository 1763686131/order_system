@echo off
echo ====================================
echo 正在停止并删除旧的 Docker 容器...
echo ====================================
docker stop my_order_app
docker rm my_order_app

echo ====================================
echo 正在重新构建 Docker 镜像...
echo ====================================
docker build -t order-backend .

echo ====================================
echo 正在启动新的 Docker 容器...
echo ====================================
docker run -d -p 7899:7899 --name my_order_app -v "%~dp0..\data":/app/data -v "%~dp0..\frontend":/app/frontend -v "%~dp0..\uploads":/app/uploads order-backend

echo ====================================
echo 启动成功！请手动打开浏览器访问 http://localhost:7899
echo ====================================
pause