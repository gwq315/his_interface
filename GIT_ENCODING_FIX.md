# Git 中文乱码修复指南

## 问题说明

在 Windows 系统上，Git 默认使用系统代码页（通常是 GBK/GB2312），导致中文提交信息显示为乱码。

## 已配置的解决方案

已为你的 Git 配置了以下设置：

```bash
# 禁用路径引用转义
git config --global core.quotepath false

# 提交信息使用 UTF-8 编码
git config --global i18n.commitencoding utf-8

# 日志输出使用 UTF-8 编码
git config --global i18n.logoutputencoding utf-8
```

## 验证配置

查看当前 Git 编码配置：

```bash
git config --global --get i18n.commitencoding
git config --global --get i18n.logoutputencoding
```

## 修复已存在的乱码提交

如果之前的提交信息有乱码，可以使用以下命令修改：

```bash
# 修改最后一次提交信息
git commit --amend -m "正确的提交信息"

# 如果已经推送到远程，需要强制推送（谨慎使用）
# git push -f origin main
```

## 后续提交

配置完成后，后续的提交信息将正确显示中文，无需额外操作。

## 查看提交信息

使用以下命令查看提交信息（确保终端支持 UTF-8）：

```bash
# 查看提交历史
git log --oneline

# 查看详细提交信息
git log -1

# 查看提交信息（UTF-8 编码）
git log --pretty=format:"%h - %an, %ar : %s" --encoding=utf-8
```

## Windows 终端编码设置

如果终端仍然显示乱码，可以设置终端使用 UTF-8：

### PowerShell

```powershell
# 临时设置（当前会话）
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001

# 永久设置（添加到 PowerShell 配置文件）
# 编辑 $PROFILE，添加：
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

### CMD

```cmd
# 临时设置（当前会话）
chcp 65001

# 永久设置（修改注册表或使用批处理文件）
```

## GitHub 显示

即使本地显示乱码，GitHub 网页上通常会正确显示中文，因为 GitHub 使用 UTF-8 编码。

## 注意事项

1. **不要强制推送已共享的提交**：如果提交已经推送到远程并被其他人使用，修改提交信息需要谨慎
2. **团队协作**：确保团队成员也配置了相同的编码设置
3. **提交信息规范**：建议使用英文提交信息，避免编码问题

## 推荐做法

为了避免编码问题，建议：

1. **使用英文提交信息**（推荐）
   ```bash
   git commit -m "Initial commit: Hospital HIS Interface Documentation Management System"
   ```

2. **在提交信息中使用英文，在代码注释中使用中文**
   - 提交信息：英文
   - 代码注释：中文（文件本身使用 UTF-8 编码）

3. **使用 Git 提交模板**
   ```bash
   git config --global commit.template ~/.gitmessage
   ```

