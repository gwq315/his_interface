# GitHub 同步指南

## 步骤 1: 在 GitHub 上创建仓库

1. 登录 GitHub (https://github.com)
2. 点击右上角的 "+" 按钮，选择 "New repository"
3. 填写仓库信息：
   - **Repository name**: `HIS_interface` (或你喜欢的名称)
   - **Description**: 医院HIS系统接口文档管理系统
   - **Visibility**: 选择 Public 或 Private
   - **不要**勾选 "Initialize this repository with a README"（因为本地已有 README）
4. 点击 "Create repository"

## 步骤 2: 添加远程仓库并推送

在项目根目录执行以下命令（将 `YOUR_USERNAME` 替换为你的 GitHub 用户名）：

```bash
# 添加远程仓库
git remote add origin https://github.com/YOUR_USERNAME/HIS_interface.git

# 或者使用 SSH（如果已配置 SSH 密钥）
# git remote add origin git@github.com:YOUR_USERNAME/HIS_interface.git

# 推送代码到 GitHub
git branch -M main
git push -u origin main
```

## 步骤 3: 验证同步

1. 刷新 GitHub 仓库页面
2. 确认所有文件都已上传

## 后续更新代码

当代码有更新时，使用以下命令同步到 GitHub：

```bash
# 查看更改
git status

# 添加更改的文件
git add .

# 提交更改（使用有意义的提交信息）
git commit -m "描述你的更改内容"

# 推送到 GitHub
git push
```

## 重要提示

### 已忽略的文件（不会上传到 GitHub）

以下文件和目录已被 `.gitignore` 忽略，**不会**上传到 GitHub：

- ✅ `venv/` - Python 虚拟环境
- ✅ `node_modules/` - Node.js 依赖
- ✅ `backend/config.ini` - 包含敏感信息的配置文件
- ✅ `uploads/` - 用户上传的文件
- ✅ `__pycache__/` - Python 缓存文件
- ✅ `.env` - 环境变量文件
- ✅ `frontend/dist/` - 前端构建产物

### 需要手动配置的文件

以下文件需要在新环境中手动创建：

1. **`backend/config.ini`** - 从 `backend/config.ini.example` 复制并修改
2. **`.env`** - 如果需要，在 `frontend/` 目录创建 `.env` 文件

### 安全建议

1. **不要**在代码中硬编码密码或敏感信息
2. **不要**提交 `config.ini` 文件（已配置忽略）
3. 使用环境变量或配置文件管理敏感信息
4. 如果仓库是 Public，确保没有泄露任何敏感数据

## 常见问题

### Q: 推送时提示需要认证？

**A:** GitHub 已不再支持密码认证，需要使用以下方式之一：

1. **Personal Access Token (推荐)**
   - 在 GitHub Settings > Developer settings > Personal access tokens 创建 token
   - 推送时使用 token 作为密码

2. **SSH 密钥**
   - 配置 SSH 密钥后使用 `git@github.com:...` 格式的 URL

### Q: 如何更新远程仓库地址？

```bash
# 查看当前远程仓库
git remote -v

# 修改远程仓库地址
git remote set-url origin https://github.com/YOUR_USERNAME/HIS_interface.git
```

### Q: 如何克隆仓库到新机器？

```bash
git clone https://github.com/YOUR_USERNAME/HIS_interface.git
cd HIS_interface
```

然后按照项目 README 中的说明进行环境配置。

