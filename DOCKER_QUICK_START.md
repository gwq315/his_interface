# Docker 快速开始指南

## 文件说明

### Docker 配置文件
- `Dockerfile.backend` - 后端服务 Docker 镜像定义
- `Dockerfile.frontend` - 前端服务 Docker 镜像定义（多阶段构建）
- `docker-compose.yml` - Docker Compose 编排配置（开发/测试环境）
- `docker-compose.prod.yml` - 生产环境扩展配置（资源限制、日志等）
- `.dockerignore` - Docker 构建时忽略的文件

### 配置文件
- `nginx.conf` - Nginx 反向代理配置（用于前端服务）
- `backend/config.ini.example` - 数据库配置模板

### 部署脚本
- `docker-deploy.sh` - Ubuntu 快速部署脚本
- `check_sqlserver_windows.ps1` - Windows SQL Server 配置检查脚本

### 文档
- `DOCKER_DEPLOY.md` - 完整部署文档（详细说明）
- `DOCKER_QUICK_START.md` - 本文件（快速参考）

## 快速部署步骤

### 1. Windows SQL Server 准备

在 Windows 主机上运行检查脚本：
```powershell
.\check_sqlserver_windows.ps1
```

根据提示配置：
- 启用 TCP/IP 协议
- 启用 SQL Server 身份验证
- 配置防火墙规则
- 记录 Windows 主机的 IP 地址

### 2. Ubuntu 服务器准备

```bash
# 安装 Docker（如果未安装）
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose（如果未安装）
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

### 3. 配置数据库连接

```bash
# 复制配置文件
cp backend/config.ini.example backend/config.ini

# 编辑配置文件
nano backend/config.ini
```

修改以下关键配置：
```ini
server = 192.168.1.100  # Windows 主机 IP
port = 1433
database = HIS_Interface
username = sa  # 或您创建的 SQL Server 用户
password = YourPassword123
odbc_driver = ODBC Driver 18 for SQL Server  # Docker 中使用 18
```

### 4. 部署应用

```bash
# 方式一：使用部署脚本（推荐）
chmod +x docker-deploy.sh
./docker-deploy.sh

# 方式二：手动部署
docker-compose build
docker-compose up -d
```

### 5. 验证部署

```bash
# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 测试后端
curl http://localhost:8000/health

# 测试前端（浏览器访问）
# http://your-ubuntu-server-ip
```

## 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend

# 查看状态
docker-compose ps

# 进入容器
docker-compose exec backend bash
docker-compose exec frontend sh

# 重新构建（代码更新后）
docker-compose build
docker-compose up -d

# 清理（删除未使用的镜像和容器）
docker system prune -a
```

## 生产环境部署

使用生产环境配置：
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

生产环境配置包括：
- 资源限制（CPU、内存）
- 日志轮转
- 自动重启策略

## 故障排查

### 无法连接数据库
1. 检查 Windows SQL Server 是否允许远程连接
2. 检查防火墙是否开放 1433 端口
3. 检查 `config.ini` 中的 IP 地址是否正确
4. 在 Ubuntu 上测试连接：`telnet <windows-ip> 1433`

### 查看详细日志
```bash
# 后端日志
docker-compose logs backend

# 前端日志
docker-compose logs frontend

# 实时日志
docker-compose logs -f
```

### 重新构建
```bash
# 清理并重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 网络架构

```
Internet
   │
   └─> Ubuntu Server (Docker)
          │
          ├─> Frontend Container (Nginx:80)
          │      └─> 代理到 Backend
          │
          └─> Backend Container (FastAPI:8000)
                 └─> 连接到 Windows SQL Server (1433)
```

## 端口说明

- **80**: 前端访问端口（Nginx）
- **8000**: 后端 API 端口（FastAPI）
- **1433**: SQL Server 端口（Windows 主机）

## 数据持久化

以下目录会被持久化（挂载到主机）：
- `./uploads` - 上传的文件
- `./backend/config.ini` - 数据库配置文件

## 安全建议

1. **生产环境**：
   - 使用 HTTPS（配置 SSL 证书）
   - 使用环境变量管理敏感信息
   - 限制数据库用户权限
   - 配置防火墙规则

2. **数据库连接**：
   - 使用强密码
   - 创建专用数据库用户（不要使用 sa）
   - 限制数据库用户权限到最小必需

3. **文件上传**：
   - 限制文件大小
   - 验证文件类型
   - 定期备份 uploads 目录

## 更多信息

详细部署说明请参考：`DOCKER_DEPLOY.md`

