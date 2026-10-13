FROM python:3.10-slim

WORKDIR /app

# Use the Tsinghua PyPI mirror for Python dependencies.
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7899

CMD ["python", "app.py"]
