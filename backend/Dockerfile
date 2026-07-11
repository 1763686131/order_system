FROM python:3.10-slim

WORKDIR /app

# 安装必要的依赖包
RUN pip install flask flask-cors

# 复制当前目录下的后端代码到容器中
COPY app.py .

# 暴露 7899 端口
EXPOSE 7899

# 运行服务
CMD ["python", "app.py"]