# Python 依赖管理说明
# Dependencies Management Guide

## 📦 依赖文件说明

### 1. requirements.txt（生产环境）
**用途**: 生产环境运行所需的最小依赖

**包含内容**:
- Flask 3.0.0 - Web 框架
- Flask-Cors 4.0.0 - 跨域支持
- Werkzeug 3.0.0 - WSGI 工具库
- python-dateutil 2.8.2 - 日期处理（可选）

**安装方法**:
```bash
pip install -r requirements.txt
```

---

### 2. requirements-dev.txt（开发环境）
**用途**: 开发和测试时使用的完整依赖

**额外包含**:
- pytest - 单元测试框架
- black - 代码格式化
- flake8 - 代码检查
- 调试和分析工具

**安装方法**:
```bash
pip install -r requirements-dev.txt
```
（会自动安装 requirements.txt 中的内容）

---

## 🚀 快速开始

### 方案一：生产环境（推荐给最终用户）

```bash
# 1. 安装最小依赖
cd e:\order_system\backend
pip install -r requirements.txt

# 2. 验证安装
pip list | findstr "Flask"

# 3. 启动服务
py app.py
```

### 方案二：开发环境（推荐给开发者）

```bash
# 1. 创建虚拟环境（推荐）
cd e:\order_system
python -m venv venv

# 2. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. 安装开发依赖
cd backend
pip install -r requirements-dev.txt

# 4. 验证安装
pip list

# 5. 启动服务
py app.py
```

---

## 📋 依赖包详细说明

### 核心依赖（生产必需）

| 包名 | 版本 | 用途 | 是否必需 |
|------|------|------|---------|
| Flask | 3.0.0 | Web 框架，构建 RESTful API | ✅ 必需 |
| Flask-Cors | 4.0.0 | 跨域资源共享，前后端分离必需 | ✅ 必需 |
| Werkzeug | 3.0.0 | Flask 依赖的 WSGI 工具库 | ✅ 必需 |
| python-dateutil | 2.8.2 | 高级日期时间处理 | ⚠️ 可选 |
| sqlite3 | 标准库 | SQLite 数据库支持 | ✅ 内置 |

### 开发工具（开发可选）

| 包名 | 版本 | 用途 | 推荐度 |
|------|------|------|--------|
| pytest | 7.4.3 | 单元测试框架 | ⭐⭐⭐⭐⭐ |
| pytest-flask | 1.3.0 | Flask 测试支持 | ⭐⭐⭐⭐ |
| pytest-cov | 4.1.0 | 测试覆盖率 | ⭐⭐⭐⭐ |
| black | 23.12.0 | 代码格式化 | ⭐⭐⭐⭐⭐ |
| flake8 | 6.1.0 | 代码质量检查 | ⭐⭐⭐⭐ |
| ipdb | 0.13.13 | 交互式调试 | ⭐⭐⭐ |

---

## 🔧 常用命令

### 依赖管理

```bash
# 安装依赖
pip install -r requirements.txt

# 更新依赖
pip install --upgrade -r requirements.txt

# 查看已安装的包
pip list

# 查看特定包信息
pip show Flask

# 冻结当前环境依赖（生成新的 requirements.txt）
pip freeze > requirements-freeze.txt

# 卸载所有依赖
pip uninstall -r requirements.txt -y
```

### 开发工具使用

```bash
# 代码格式化（推荐）
black backend/

# 代码检查
flake8 backend/ --max-line-length=100

# 运行测试
pytest

# 测试覆盖率
pytest --cov=backend --cov-report=html

# 查看覆盖率报告
start htmlcov/index.html  # Windows
# open htmlcov/index.html  # Mac
```

---

## 🐍 Python 版本要求

- **最低版本**: Python 3.8
- **推荐版本**: Python 3.10 或 3.11
- **测试版本**: Python 3.11

### 检查 Python 版本

```bash
# Windows
py --version

# Linux/Mac
python3 --version
```

---

## 🌐 虚拟环境（强烈推荐）

### 为什么使用虚拟环境？

1. ✅ 隔离项目依赖，避免版本冲突
2. ✅ 不污染全局 Python 环境
3. ✅ 便于部署和迁移
4. ✅ 便于团队协作

### 创建和使用虚拟环境

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# 3. 确认已激活（命令提示符前会显示 (venv)）
which python  # Linux/Mac
where python  # Windows

# 4. 安装依赖
pip install -r requirements.txt

# 5. 退出虚拟环境
deactivate
```

---

## ❓ 常见问题

### Q1: pip 安装很慢怎么办？

**A**: 使用国内镜像源

```bash
# 临时使用
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 永久设置
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q2: 提示权限错误怎么办？

**A**: 使用虚拟环境或添加 --user 参数

```bash
# 方案一：使用虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 方案二：安装到用户目录
pip install --user -r requirements.txt
```

### Q3: 如何更新某个包？

**A**: 使用 --upgrade 参数

```bash
# 更新单个包
pip install --upgrade Flask

# 更新所有包
pip install --upgrade -r requirements.txt
```

### Q4: SQLite 需要单独安装吗？

**A**: 不需要，sqlite3 是 Python 标准库的一部分

验证方法：
```bash
python -c "import sqlite3; print(sqlite3.version)"
```

### Q5: 如何在不同环境间切换？

**A**: 使用不同的虚拟环境

```bash
# 生产环境
python -m venv venv-prod
venv-prod\Scripts\activate
pip install -r requirements.txt

# 开发环境
python -m venv venv-dev
venv-dev\Scripts\activate
pip install -r requirements-dev.txt
```

---

## 📦 依赖包大小参考

### 生产环境（requirements.txt）
```
Flask            : ~1.5 MB
Flask-Cors       : ~50 KB
Werkzeug         : ~700 KB
python-dateutil  : ~300 KB
-----------------------------
总计             : ~2.5 MB
```

### 开发环境（requirements-dev.txt）
```
生产依赖         : ~2.5 MB
pytest 及插件    : ~5 MB
代码质量工具      : ~3 MB
调试工具         : ~2 MB
-----------------------------
总计             : ~12.5 MB
```

---

## 🔄 依赖更新日志

### 2026-09-06
- ✅ 初始版本创建
- ✅ Flask 3.0.0
- ✅ Flask-Cors 4.0.0
- ✅ 添加开发依赖文件（requirements-dev.txt）
- ✅ 添加详细注释和说明

---

## 📚 相关文档

- [Flask 官方文档](https://flask.palletsprojects.com/)
- [pip 用户指南](https://pip.pypa.io/en/stable/user_guide/)
- [Python 虚拟环境指南](https://docs.python.org/3/library/venv.html)
- [SQLite Python 文档](https://docs.python.org/3/library/sqlite3.html)

---

## 💡 最佳实践

1. ✅ **始终使用虚拟环境**
2. ✅ **固定版本号**（避免使用 >= 或 ~=）
3. ✅ **定期更新依赖包**（安全更新）
4. ✅ **区分生产和开发依赖**
5. ✅ **使用镜像源加速安装**（国内环境）
6. ✅ **版本控制排除 venv/**（添加到 .gitignore）

---

**最后更新**: 2026-09-06  
**维护者**: 订单管理系统开发团队
