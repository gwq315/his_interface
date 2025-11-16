# SQL Server数据库配置指南

## 一、安装ODBC驱动（使用pyodbc时）

### Windows系统

1. 下载ODBC驱动：
   - 访问：https://docs.microsoft.com/zh-cn/sql/connect/odbc/download-odbc-driver-for-sql-server
   - 下载并安装 "ODBC Driver 17 for SQL Server" 或更高版本

2. 验证安装：
   ```cmd
   odbcinst -q -d
   ```
   应该能看到已安装的SQL Server驱动

### Linux系统

1. Ubuntu/Debian:
   ```bash
   curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
   curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list
   apt-get update
   ACCEPT_EULA=Y apt-get install -y msodbcsql17
   ```

2. RHEL/CentOS:
   ```bash
   curl https://packages.microsoft.com/config/rhel/8/prod.repo > /etc/yum.repos.d/mssql-release.repo
   ACCEPT_EULA=Y yum install -y msodbcsql17
   ```

### macOS系统

```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
HOMEBREW_NO_ENV_FILTERING=1 ACCEPT_EULA=Y brew install msodbcsql17 mssql-tools
```

## 二、配置文件说明

### config.ini文件结构

```ini
[Database]
# 数据库驱动类型
driver = mssql+pyodbc              # 或 mssql+pymssql

# 服务器信息
server = localhost                 # SQL Server服务器地址
port = 1433                       # 端口号

# 数据库信息
database = HIS_Interface          # 数据库名称

# 认证信息
username = sa                     # 用户名
password = YourPassword123        # 密码

# ODBC驱动（使用pyodbc时必需）
odbc_driver = ODBC Driver 17 for SQL Server

# 连接参数
timeout = 30                      # 连接超时时间（秒）
use_windows_auth = False          # 是否使用Windows身份验证
```

### 配置选项说明

| 配置项 | 说明 | 示例 |
|--------|------|------|
| driver | 数据库驱动类型 | `mssql+pyodbc` 或 `mssql+pymssql` |
| server | SQL Server服务器地址 | `localhost`、`192.168.1.100`、`server.example.com` |
| port | 端口号 | `1433`（默认） |
| database | 数据库名称 | `HIS_Interface` |
| username | 登录用户名 | `sa` |
| password | 登录密码 | `YourPassword123` |
| odbc_driver | ODBC驱动名称 | `ODBC Driver 17 for SQL Server` |
| timeout | 连接超时时间（秒） | `30` |
| use_windows_auth | Windows身份验证 | `True` 或 `False` |

## 三、使用Windows身份验证

如果使用Windows身份验证，配置如下：

```ini
[Database]
driver = mssql+pyodbc
server = localhost
port = 1433
database = HIS_Interface
use_windows_auth = True
odbc_driver = ODBC Driver 17 for SQL Server
```

**注意：**
- `use_windows_auth = True` 时，`username` 和 `password` 会被忽略
- 运行程序的Windows用户必须有SQL Server访问权限
- 确保SQL Server配置为支持混合身份验证或Windows身份验证

## 四、创建数据库

在SQL Server Management Studio (SSMS) 或使用命令行创建数据库：

```sql
-- 使用SQL Server身份验证
CREATE DATABASE HIS_Interface;
GO

-- 或使用Windows身份验证
-- 确保当前Windows用户有创建数据库的权限
CREATE DATABASE HIS_Interface;
GO
```

## 五、常见问题

### 1. 连接失败：无法找到ODBC驱动

**解决方案：**
- 检查是否安装了ODBC驱动
- 在Windows上运行 `odbcinst -q -d` 查看已安装的驱动
- 确保config.ini中的`odbc_driver`名称与已安装的驱动名称完全一致
- 或者使用pymssql驱动（不需要ODBC驱动）

### 2. 连接失败：用户登录失败

**解决方案：**
- 检查用户名和密码是否正确
- 确认SQL Server允许SQL Server身份验证
- 检查用户是否有访问数据库的权限
- 如果使用Windows身份验证，确保Windows用户有权限

### 3. 连接超时

**解决方案：**
- 检查服务器地址和端口是否正确
- 检查防火墙设置
- 增加timeout值
- 检查SQL Server服务是否运行

### 4. 数据库不存在

**解决方案：**
- 先创建数据库（见第四部分）
- 检查数据库名称是否正确
- 确认用户有访问该数据库的权限

## 六、测试连接

可以通过Python脚本测试数据库连接：

```python
from sqlalchemy import create_engine, text

# 读取配置（需要先设置好config.ini）
from backend.database import SQLALCHEMY_DATABASE_URL

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT @@VERSION"))
        print("连接成功！")
        print(f"SQL Server版本: {result.fetchone()[0]}")
except Exception as e:
    print(f"连接失败: {e}")
```

## 七、安全建议

1. **不要将config.ini提交到版本控制系统**
   - config.ini已添加到.gitignore
   - 使用config.ini.example作为模板

2. **使用强密码**
   - 密码应包含大小写字母、数字和特殊字符
   - 定期更换密码

3. **限制数据库用户权限**
   - 不要使用sa账户（生产环境）
   - 创建专用数据库用户，只授予必要权限

4. **使用Windows身份验证（如果可能）**
   - 更安全，不需要在配置文件中存储密码

5. **加密连接**
   - 生产环境建议使用SSL/TLS加密连接

