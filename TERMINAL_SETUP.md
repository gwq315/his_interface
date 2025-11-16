# VS Code/Cursor 终端配置指南

## 为什么需要切换到CMD？

本项目已统一使用CMD批处理脚本（`.bat`文件），包括：
- `setup_venv.bat` - 创建虚拟环境
- `start_backend.bat` - 启动后端服务
- `start_frontend.bat` - 启动前端服务
- `activate_venv.bat` - 激活虚拟环境

为确保开发环境一致性，建议将VS Code/Cursor的默认终端设置为CMD。

## 配置方法

### 方法一：使用项目配置文件（推荐）

项目已包含 `.vscode/settings.json` 配置文件，会自动将默认终端设置为CMD。

**如果配置文件已存在**：
- 重启VS Code/Cursor后会自动生效
- 或者手动执行：`Ctrl+Shift+P` -> `Terminal: Reload Window`

**如果配置文件不存在**：
- 项目根目录下已创建 `.vscode/settings.json`
- 重启VS Code/Cursor即可

### 方法二：手动配置

1. **打开设置**
   - 按 `Ctrl+,` 打开设置
   - 或点击：文件 -> 首选项 -> 设置

2. **搜索终端配置**
   - 在搜索框中输入：`terminal.integrated.defaultProfile.windows`

3. **设置默认终端**
   - 选择 `terminal.integrated.defaultProfile.windows`
   - 从下拉菜单中选择：`Command Prompt`

4. **验证配置**
   - 按 `` Ctrl+` `` 打开新终端
   - 终端标题应显示 "Command Prompt" 或 "cmd"

### 方法三：临时切换终端

如果想临时切换到CMD（不修改默认设置）：

1. **打开终端选择器**
   - 点击终端下拉箭头（终端标题栏右侧）
   - 或按 `Ctrl+Shift+P` -> `Terminal: Select Default Profile`

2. **选择CMD**
   - 选择 "Command Prompt"

## 验证配置

打开新终端后，应该看到：

```
Microsoft Windows [版本 ...]
(c) Microsoft Corporation。保留所有权利。

D:\Python\CursorPy\HIS_interface>
```

而不是PowerShell的提示符（`PS D:\...>`）。

## 测试脚本

运行以下命令测试CMD终端：

```cmd
echo %PATH%
where python
setup_venv.bat
```

如果命令正常执行且中文显示正常，说明配置成功。

## 常见问题

### Q: 配置后还是PowerShell？

A: 
1. 完全关闭VS Code/Cursor并重新打开
2. 检查 `.vscode/settings.json` 文件是否存在且格式正确
3. 手动选择终端：点击终端下拉箭头 -> 选择 "Command Prompt"

### Q: 如何切换回PowerShell？

A: 
1. 修改 `.vscode/settings.json` 中的 `terminal.integrated.defaultProfile.windows` 为 `PowerShell`
2. 或临时在终端选择器中选择PowerShell

### Q: 团队协作时每个人都要配置吗？

A: 
- 如果项目包含 `.vscode/settings.json`，团队成员打开项目后会自动应用配置
- 首次打开时可能需要重启VS Code/Cursor

### Q: CMD和PowerShell的区别？

A: 
- **CMD**: 传统Windows命令提示符，语法简单，适合批处理脚本
- **PowerShell**: 功能更强大，但语法不同，执行策略可能受限

本项目使用CMD是因为：
- 所有脚本都是`.bat`格式，专为CMD设计
- CMD执行策略更宽松，无需额外配置
- 与Windows系统集成更好

## 配置文件说明

`.vscode/settings.json` 包含以下配置：

```json
{
  // 默认终端为CMD
  "terminal.integrated.defaultProfile.windows": "Command Prompt",
  
  // CMD终端配置
  "terminal.integrated.profiles.windows": {
    "Command Prompt": {
      "path": ["${env:windir}\\System32\\cmd.exe"]
    }
  },
  
  // Python虚拟环境自动激活
  "python.terminal.activateEnvironment": true
}
```

## 注意事项

1. **文件编码**: 确保`.bat`文件以UTF-8 with BOM保存（见`CMD_ENCODING.md`）
2. **权限问题**: CMD脚本可能需要的权限比PowerShell低
3. **兼容性**: 某些PowerShell特有功能在CMD中不可用

## 相关文档

- `CMD_ENCODING.md` - CMD脚本编码说明
- `README.md` - 项目快速开始指南

