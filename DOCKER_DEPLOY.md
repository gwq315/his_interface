# Docker 部署方案

本文档说明如何将项目部署到 Ubuntu 24.04 的 Docker 环境中，同时连接 Windows 主机上的 SQL Server 数据库。

## 前置要求

### Ubuntu 24.04 服务器
- Docker 20.10+
- Docker Compose 2.0+
- 网络能够访问 Windows 主机的 SQL Server（端口 1433）

### Windows 主机（SQL Server）
- SQL Server 已启用 TCP/IP 协议
- SQL Server 允许远程连接
- 防火墙开放 1433 端口
- 确保有 SQL Server 身份验证的用户（或配置 Windows 身份验证）

## 部署步骤

### 1. 准备项目文件

将项目文件上传到 Ubuntu 服务器，确保包含以下目录结构：
```
HIS_interface/
├── backend/
│   ├── app/
│   ├── config.ini.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── package.json
├── uploads/
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
├── nginx.conf
└── .dockerignore
```

### 2. 配置数据库连接

#### 方式一：使用配置文件（推荐）

1. 复制配置文件模板：
```bash
cp backend/config.ini.example backend/config.ini
```

2. 编辑 `backend/config.ini`，修改数据库连接信息：

```ini
[Database]
driver = mssql+pyodbc
# 重要：使用 Windows 主机的 IP 地址或主机名
# 如果 Docker 容器和 Windows 在同一网络，可以使用 Windows 主机的局域网 IP
# 例如：192.168.1.100 或 windows-hostname
server = 192.168.1.100  # 替换为 Windows 主机的实际 IP
port = 1433
database = HIS_Interface
username = sa  # SQL Server 用户名
password = YourPassword123  # SQL Server 密码
odbc_driver = ODBC Driver 18 for SQL Server
timeout = 30
use_windows_auth = False
```

**重要说明：**
- `server` 字段必须填写 Windows 主机的实际 IP 地址或主机名
- 如果 Docker 运行在 Ubuntu 上，Windows 主机在同一局域网，使用 Windows 的局域网 IP
- 如果 Windows 主机有防火墙，需要确保允许来自 Ubuntu 服务器的连接

#### 方式二：使用环境变量

在 `docker-compose.yml` 中取消注释并修改 `DATABASE_URL` 环境变量：

```yaml
environment:
  DATABASE_URL: "mssql+pyodbc://username:password@192.168.1.100:1433/HIS_Interface?driver=ODBC+Driver+18+for+SQL+Server"
```

### 3. 配置 Windows SQL Server 允许远程连接

#### 3.1 启用 TCP/IP 协议

1. 打开 SQL Server Configuration Manager
2. 展开 "SQL Server 网络配置"
3. 选择 "MSSQLSERVER 的协议"
4. 右键点击 "TCP/IP"，选择 "启用"
5. 双击 "TCP/IP"，在 "IP 地址" 选项卡中：
   - 找到 "IPAll" 部分
   - 确保 "TCP 端口" 为 1433
   - 如果 "TCP 动态端口" 有值，清空它
6. 重启 SQL Server 服务

#### 3.2 启用 SQL Server 身份验证

1. 打开 SQL Server Management Studio (SSMS)
2. 连接到 SQL Server 实例
3. 右键点击服务器，选择 "属性"
4. 在 "安全性" 页面：
   - 选择 "SQL Server 和 Windows 身份验证模式"
5. 点击 "确定" 并重启 SQL Server 服务

#### 3.3 创建 SQL Server 登录用户（如果使用 SQL Server 身份验证）

```sql
-- 创建登录用户
CREATE LOGIN docker_user WITH PASSWORD = 'YourStrongPassword123!';

-- 授予数据库访问权限
USE HIS_Interface;
CREATE USER docker_user FOR LOGIN docker_user;

-- 授予必要权限
ALTER ROLE db_owner ADD MEMBER docker_user;
```

#### 3.4 配置 Windows 防火墙

1. 打开 Windows 防火墙
2. 添加入站规则：
   - 规则类型：端口
   - 协议：TCP
   - 端口：1433
   - 操作：允许连接
   - 配置文件：全部
   - 名称：SQL Server 1433

### 4. 测试网络连接

在 Ubuntu 服务器上测试能否连接到 Windows SQL Server：

```bash
# 安装 telnet 或使用 nc (netcat)
sudo apt-get install telnet

# 测试连接（替换为 Windows 主机 IP）
telnet 192.168.1.100 1433
```

如果连接成功，说明网络是通的。

### 5. 构建和启动 Docker 容器

```bash
# 进入项目目录
cd /path/to/HIS_interface

# 构建镜像（首次运行或代码更新后）
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 6. 验证部署

1. **检查容器状态**：
```bash
docker-compose ps
```

应该看到两个容器都在运行：
- `his-interface-backend`
- `his-interface-frontend`

2. **测试后端 API**：
```bash
curl http://localhost:8000/health
```

应该返回：`{"status":"ok"}`

3. **测试前端**：
在浏览器中访问：`http://your-ubuntu-server-ip`

4. **查看 API 文档**：
访问：`http://your-ubuntu-server-ip:8000/docs`

### 7. 常见问题排查

#### 问题1：无法连接到 SQL Server

**症状**：后端日志显示连接超时或拒绝连接

**解决方案**：
1. 检查 Windows SQL Server 是否允许远程连接
2. 检查 Windows 防火墙是否开放 1433 端口
3. 检查 `config.ini` 中的 `server` 地址是否正确
4. 在 Ubuntu 服务器上测试网络连接：
   ```bash
   telnet <windows-ip> 1433
   ```

#### 问题2：ODBC 驱动错误

**症状**：日志显示 "ODBC Driver 18 for SQL Server" 未找到

**解决方案**：
- 检查 Dockerfile.backend 是否正确安装了 ODBC 驱动
- 重新构建镜像：`docker-compose build --no-cache backend`

#### 问题3：权限错误

**症状**：数据库操作失败，提示权限不足

**解决方案**：
- 确保 SQL Server 用户有足够的权限
- 检查数据库用户是否已添加到数据库并授予权限

#### 问题4：前端无法访问后端 API

**症状**：前端页面显示 API 错误

**解决方案**：
1. 检查 nginx 配置是否正确
2. 检查 docker-compose.yml 中的网络配置
3. 查看前端容器日志：`docker-compose logs frontend`
4. 检查后端是否正常运行：`docker-compose logs backend`

### 8. 生产环境优化建议

#### 8.1 使用环境变量管理敏感信息

创建 `.env` 文件（不要提交到版本控制）：
```env
DB_SERVER=192.168.1.100
DB_PORT=1433
DB_NAME=HIS_Interface
DB_USER=sa
DB_PASSWORD=YourPassword123
```

在 `docker-compose.yml` 中使用：
```yaml
environment:
  DATABASE_URL: "mssql+pyodbc://${DB_USER}:${DB_PASSWORD}@${DB_SERVER}:${DB_PORT}/${DB_NAME}?driver=ODBC+Driver+18+for+SQL+Server"
```

#### 8.2 使用 Docker Secrets（Docker Swarm）

对于更安全的配置，可以使用 Docker Secrets。

#### 8.3 配置 HTTPS

1. 使用 Nginx 反向代理配置 SSL
2. 或使用 Traefik/Let's Encrypt 自动证书

#### 8.4 数据备份

定期备份 `uploads` 目录和数据库：
```bash
# 备份上传文件
tar -czf uploads-backup-$(date +%Y%m%d).tar.gz uploads/

# 备份数据库（在 Windows 上）
# 使用 SQL Server Management Studio 或命令行工具
```

#### 8.5 监控和日志

- 配置日志轮转
- 使用 Docker 日志驱动
- 集成监控系统（如 Prometheus + Grafana）

### 9. 更新和维护

#### 更新代码
```bash
# 拉取最新代码
git pull

# 重新构建并重启
docker-compose build
docker-compose up -d

# 查看更新后的日志
docker-compose logs -f
```

#### 查看容器资源使用
```bash
docker stats
```

#### 进入容器调试
```bash
# 进入后端容器
docker-compose exec backend bash

# 进入前端容器
docker-compose exec frontend sh
```

#### 停止和清理
```bash
# 停止服务
docker-compose down

# 停止并删除卷（注意：会删除数据）
docker-compose down -v

# 清理未使用的镜像
docker system prune -a
```

## 网络配置说明

### Docker 网络模式

默认情况下，`docker-compose.yml` 使用 `bridge` 网络模式。容器之间可以通过服务名（`backend`、`frontend`）相互访问。

### 访问 Windows SQL Server

Docker 容器访问 Windows 主机上的 SQL Server 有几种方式：

1. **使用 Windows 主机 IP 地址**（推荐）
   - 在 `config.ini` 中使用 Windows 主机的局域网 IP
   - 例如：`server = 192.168.1.100`

2. **使用 host.docker.internal**（仅限 Docker Desktop）
   - 如果使用 Docker Desktop，可以使用 `host.docker.internal`
   - 在 Linux 上需要额外配置

3. **使用 host 网络模式**（不推荐）
   - 容器直接使用主机网络
   - 可能有安全风险

### 防火墙配置

确保以下端口开放：
- **80**: 前端访问
- **8000**: 后端 API（如果直接访问）
- **1433**: SQL Server（从 Ubuntu 到 Windows）

## 总结

完成以上步骤后，您的应用应该能够：
- ✅ 在 Ubuntu 24.04 的 Docker 中运行
- ✅ 连接到 Windows 主机上的 SQL Server
- ✅ 通过浏览器访问前端界面
- ✅ 通过 API 访问后端服务

如有问题，请查看容器日志进行排查。

