# 📦 工业级订单管理看板系统 (Local Order Board)

> 🚀 **专为无网工业/仓储环境打造的极简、高可用、触摸屏友好的业务流转系统**

这是一个完全**零外部依赖**、针对厂区内网环境进行极致优化的订单与业务流转控制中枢。它不仅具备极高颜值的现代化 UI（3D卡片、时间线排版、玻璃拟物态），更内置了严密的“三级岗位防呆隔离”机制。开箱即用，支持 Windows 一键启动与 NAS/Docker 稳健部署。

---

## ✨ 核心亮点 (Core Features)

### 🛡️ 1. 100% 纯本地运行，永不瘫痪
* **零外网依赖**：彻底剥离所有外部 CDN（无外链 Vue/Axios/Bootstrap），纯原生 JavaScript + CSS 构建，厂区断网照样丝滑运行。
* **原生 Python Flask 驱动**：极其轻量级的后端 JSON 文件读写引擎，数据响应低延迟，完美适配大小写敏感的 Linux/Docker 容器。

### 🎨 2. 次世代现代化交互 UI
* **工业触摸屏调优 (Kiosk Ready)**：针对 1080P 车间显示屏深度像素级重构，彻底屏蔽浏览器双指缩放、右键菜单与长按误触。
* **高颜值数据看板**：引入 3D 翻转卡片、朋友圈式物流时间线、高质感莫兰迪色系大药丸按钮。
* **NOMI 智能悬浮球**：右下角常驻全局控制中枢，支持精细化的呼吸动画与点击失焦收起交互。

### 🚚 3. 智能物流与回单管理
* **AI 记忆词云**：发货审核时分离“物流公司”与“物流单号”，系统自动记忆物流公司并生成快捷点击标签（智能判定“专车”模式并自动过滤防污染）。
* **物理级图像矫正**：前端集成 Canvas 画布引擎，支持回单图片上传前直接通过中心磨砂按钮进行物理角度旋转矫正。
* **画廊级安全预览**：支持高清回单无损放大预览（Lightbox），权限隔离下支持图片一键下载与真实的物理粉碎删除。

### ⚙️ 4. 动态数据驱动架构 (State-Driven)
* **状态复用引擎**：弹窗底层逻辑全面重构，同一个容器可根据不同操作（如：审核模式 / 回单模式）无缝切换展示内部表单与控件结构，告别冗余 HTML。

---

## 👥 权限隔离架构 (Roles & Permissions)

系统内置极其严格的细粒度三级权限体系：

- 👑 **超级管理员 (super_admin)**
  - 拥有整个系统的“生杀大权”。
  - **专属功能**：进入账户控制台创建/删除员工账号、重置密码；控制全局物料流水的物理修改；拥有真实数据的“彻底粉碎”权限。
- 💼 **管理员 (admin)**
  - 仓储核心调度者。
  - **专属功能**：可查看全量大盘数据；拥有创建新订单、修改业务备注、确认出库审核、上传物流单号等推进流转权限。
- 👷 **操作员 (operator)**
  - 一线执行者。
  - **专属功能**：仅能查看当前时间视窗内的“未完成订单”，无权干涉或查看历史敏感流水，系统提供绝对的安全防呆隔离。

---

## 🚀 极速部署指南 (Deployment)

系统提供两种标准的部署方案，无论是一台普通旧电脑还是专业服务器均可完美胜任。

### 方案 A：Windows 本地快速启动 (适合小白)
1. 确保电脑已安装 Python 3.8+ 环境和Docker Desktop软件。
2. 进入 `backend` 文件夹。
3. 双击运行 `run.bat`。系统将自动安装依赖并唤起默认浏览器全屏展示。

### 方案 B：NAS / 服务器 Docker 部署 (推荐工业级使用)
推荐在 群晖 / 威联通 / 绿联 或 Linux 服务器上使用 Docker Compose 进行稳健部署：

```yaml
version: '3'

services:
  order-board:
    image: python:3.10-slim
    container_name: nas_order_board
    ports:
      - "7899:7899"
    volumes:
      # ⚠️ 请将冒号前的路径修改为你服务器上对应的绝对物理路径
      - /your/path/order_system/backend:/app
      - /your/path/order_system/data:/app/data
      - /your/path/order_system/frontend:/app/frontend
    working_dir: /app
    # 🎯 强力矫正：注入北京东八区时区，确保发单与完成时戳精确无误
    environment:
      - TZ=Asia/Shanghai
    command: sh -c "pip install flask flask-cors -i [https://pypi.tuna.tsinghua.edu.cn/simple](https://pypi.tuna.tsinghua.edu.cn/simple) && python app.py"
    restart: always
```

```Plaintext
order_system/
├── frontend/             # 前端静态资源 (纯净解耦，修改即生效)
│   ├── index.html        # 全局唯一视图骨架
│   ├── css/
│   │   ├── style.css     # 核心功能与弹窗排版样式
│   │   ├── theme.css     # 全局原子级主题颜色变量库
│   │   └── nomi.css      # NOMI 悬浮球专项动画样式
│   └── js/
│       ├── main.js       # 核心业务请求与卡片渲染引擎
│       ├── tools.js      # 全局纯净黑盒工具函数库
│       └── users.js      # 细粒度权限配置与用户校验模块
├── backend/              # 后端服务
│   ├── app.py            # Flask 路由请求拦截与 JSON 读写中枢
│   └── run.bat           # Windows 守护启动脚本
└── data/                 # 📂 数据库持久化目录 (极其重要，需定期备份！)
    ├── orders_db.json    # 订单大盘主数据库
    ├── users_db.json     # 账号密码及权限控制表
    ├── material_db.json  # 物料消耗明细库
    └── carrier_tags.json # [系统自学习] 物流快捷历史词云库
```
