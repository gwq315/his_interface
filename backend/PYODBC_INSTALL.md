# pyodbc安装问题解决方案

## 问题描述

在Python 3.13下安装pyodbc时可能遇到编译错误：
```
error C2660: 'PyLong_AsByteArray': 函数不接受 5 个参数
```

这是因为Python 3.13更改了部分C API，而pyodbc的某些版本还未适配。

## 解决方案

### 方案1：使用预编译的wheel文件（推荐）

如果pip找不到预编译的wheel，可以尝试：

```cmd
pip install pyodbc --only-binary :all:
```

或者手动下载wheel文件：

1. 访问：https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyodbc
2. 下载对应Python版本的wheel文件（如：pyodbc-5.0.1-cp313-cp313-win_amd64.whl）
3. 安装：
   ```cmd
   pip install pyodbc-5.0.1-cp313-cp313-win_amd64.whl
   ```

### 方案2：使用pymssql（无需ODBC驱动）

修改 `backend/requirements.txt`：

```txt
# 注释掉pyodbc
# pyodbc>=5.0.1

# 取消注释pymssql
pymssql==2.2.11
```

然后重新安装：

```cmd
pip install -r requirements.txt
```

**注意**：使用pymssql时需要修改 `backend/database.py` 中的驱动配置：
- 将 `driver = mssql+pyodbc` 改为 `driver = mssql+pymssql`
- 移除ODBC相关配置

### 方案3：降级Python版本

如果以上方案都不行，可以降级到Python 3.11或3.12：

1. 下载并安装Python 3.11或3.12
2. 重新创建虚拟环境：
   ```cmd
   setup_venv.bat
   ```

### 方案4：等待pyodbc更新

关注pyodbc的GitHub仓库：
- https://github.com/mkleehammer/pyodbc/issues

等待官方发布支持Python 3.13的版本。

## 验证安装

安装成功后，验证：

```python
import pyodbc
print(pyodbc.version)
```

或者：

```python
import pymssql
print(pymssql.__version__)
```

## 常见问题

### Q: 为什么Python 3.13会有这个问题？

A: Python 3.13引入了新的C API变化，一些C扩展模块需要更新才能兼容。

### Q: 使用pymssql有什么限制？

A: 
- 不需要ODBC驱动，安装更简单
- 功能相对较少，某些高级特性可能不支持
- 性能可能略低于pyodbc

### Q: 如何判断应该使用哪个驱动？

A: 
- 如果系统已安装ODBC驱动，优先使用pyodbc
- 如果需要快速部署，使用pymssql
- 如果需要完整功能，使用pyodbc

## 相关文档

- `backend/DATABASE_SETUP.md` - 数据库配置指南
- `README.md` - 项目快速开始指南

