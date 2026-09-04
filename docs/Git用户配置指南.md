# Git 用户配置指南

## 🎯 配置 Git 用户名和邮箱

### 方法 1：全局配置（推荐）

全局配置会应用到你电脑上所有的 Git 项目。

```bash
# 配置用户名
git config --global user.name "你的名字"

# 配置邮箱
git config --global user.email "your.email@example.com"
```

**示例**：
```bash
git config --global user.name "张三"
git config --global user.email "zhangsan@example.com"
```

---

### 方法 2：单个项目配置

如果只想为当前项目配置，去掉 `--global` 参数：

```bash
# 进入项目目录
cd e:/order_system

# 配置用户名（仅当前项目）
git config user.name "你的名字"

# 配置邮箱（仅当前项目）
git config user.email "your.email@example.com"
```

---

## 🔍 查看当前配置

### 查看全局配置
```bash
git config --global user.name
git config --global user.email
```

### 查看当前项目配置
```bash
git config user.name
git config user.email
```

### 查看所有配置
```bash
# 全局配置
git config --global --list

# 当前项目配置
git config --list
```

---

## 📝 完整配置示例

### 场景 1：第一次使用 Git

```bash
# 1. 配置用户名
git config --global user.name "张三"

# 2. 配置邮箱
git config --global user.email "zhangsan@qq.com"

# 3. 验证配置
git config --global user.name
git config --global user.email

# 4. 查看所有配置
git config --global --list
```

---

### 场景 2：为订单系统项目单独配置

```bash
# 1. 进入项目目录
cd e:/order_system

# 2. 配置项目专用的用户名和邮箱
git config user.name "订单系统开发者"
git config user.email "order-dev@company.com"

# 3. 验证配置
git config user.name
git config user.email
```

---

## ⚙️ 其他常用 Git 配置

### 配置默认编辑器
```bash
# 使用 VS Code
git config --global core.editor "code --wait"

# 使用 Notepad++
git config --global core.editor "'C:/Program Files/Notepad++/notepad++.exe' -multiInst -notabbar -nosession -noPlugin"
```

### 配置换行符（Windows 推荐）
```bash
git config --global core.autocrlf true
```

### 配置颜色显示
```bash
git config --global color.ui auto
```

### 配置别名（快捷命令）
```bash
# 配置 git st 代替 git status
git config --global alias.st status

# 配置 git co 代替 git checkout
git config --global alias.co checkout

# 配置 git br 代替 git branch
git config --global alias.br branch

# 配置 git ci 代替 git commit
git config --global alias.ci commit
```

---

## 🔧 修改已有配置

### 修改用户名
```bash
git config --global user.name "新的名字"
```

### 修改邮箱
```bash
git config --global user.email "new.email@example.com"
```

---

## 🗑️ 删除配置

### 删除全局配置
```bash
git config --global --unset user.name
git config --global --unset user.email
```

### 删除当前项目配置
```bash
git config --unset user.name
git config --unset user.email
```

---

## 📍 配置文件位置

### 全局配置文件
- **Windows**: `C:\Users\你的用户名\.gitconfig`
- **Mac/Linux**: `~/.gitconfig`

### 项目配置文件
- 位置: `项目目录/.git/config`
- 示例: `e:\order_system\.git\config`

你也可以直接编辑这些文件来修改配置。

---

## ✅ 验证配置是否成功

### 方法 1：查看配置
```bash
git config --global user.name
git config --global user.email
```

### 方法 2：查看配置文件
```bash
# Windows
cat C:\Users\你的用户名\.gitconfig

# Mac/Linux
cat ~/.gitconfig
```

### 方法 3：尝试提交
```bash
# 创建一个测试提交
git add .
git commit -m "测试提交"

# 查看提交信息
git log -1
```

应该能看到你配置的用户名和邮箱。

---

## 🎯 推荐配置（完整版）

如果是第一次配置 Git，推荐执行以下命令：

```bash
# 1. 配置用户信息
git config --global user.name "你的名字"
git config --global user.email "your.email@example.com"

# 2. 配置换行符处理（Windows）
git config --global core.autocrlf true

# 3. 配置颜色显示
git config --global color.ui auto

# 4. 配置编辑器（可选）
git config --global core.editor "code --wait"

# 5. 配置别名（可选）
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.last "log -1 HEAD"

# 6. 验证配置
git config --global --list
```

---

## 💡 常见问题

### Q1: 配置后提交时还是提示没有配置用户名？
**A**: 可能是当前项目有单独配置覆盖了全局配置。解决方法：
```bash
cd e:/order_system
git config user.name "你的名字"
git config user.email "your.email@example.com"
```

### Q2: 如何查看是使用的全局配置还是项目配置？
**A**: 使用以下命令：
```bash
git config --show-origin user.name
git config --show-origin user.email
```

### Q3: 忘记配置了什么用户名？
**A**: 查看配置：
```bash
git config user.name
```

### Q4: 能否为不同项目配置不同的用户信息？
**A**: 可以！在每个项目目录下执行：
```bash
cd 项目目录
git config user.name "项目A的名字"
git config user.email "projectA@example.com"
```

---

## 🚀 快速开始

如果你现在就想配置，复制并修改以下命令：

```bash
# 替换为你自己的信息
git config --global user.name "张三"
git config --global user.email "zhangsan@example.com"

# 验证
git config --global user.name
git config --global user.email
```

---

## 📞 需要帮助？

如果配置过程中遇到问题，可以：
1. 查看 Git 帮助：`git config --help`
2. 查看配置手册：`git help config`
3. 检查配置文件：打开 `~/.gitconfig`（全局）或 `.git/config`（项目）
