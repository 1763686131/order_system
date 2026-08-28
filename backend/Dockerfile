FROM python:3.10-slim

WORKDIR /app

# 配置pip使用国内镜像源（清华大学镜像）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装必要的依赖包
RUN pip install flask flask-cors

# 复制当前目录下的后端代码到容器中
COPY app.py .

# 暴露 7899 端口
EXPOSE 7899

# 运行服务
CMD ["python", "app.py"]