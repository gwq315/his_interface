# 修复 413 Request Entity Too Large 错误

## 问题说明

413 错误表示请求实体太大，通常是因为 Nginx 或 Web 服务器的文件大小限制。

## 检查步骤

### 1. 检查后端服务器是否有独立的 Nginx

如果后端在 Ubuntu 服务器上，并且有独立的 Nginx 反向代理，需要检查：

```bash
# 在 Ubuntu 服务器上执行
sudo nginx -t
sudo cat /etc/nginx/nginx.conf | grep client_max_body_size
sudo cat /etc/nginx/sites-enabled/* | grep client_max_body_size
```

### 2. 修复 Ubuntu 服务器上的 Nginx 配置

如果发现 Ubuntu 服务器上有独立的 Nginx，需要修改配置：

```bash
# 编辑 Nginx 主配置文件
sudo nano /etc/nginx/nginx.conf

# 在 http 块中添加或修改：
http {
    client_max_body_size 100M;
    ...
}

# 或者在具体的 server 块中添加：
server {
    client_max_body_size 100M;
    ...
}
```

然后重启 Nginx：

```bash
sudo nginx -t  # 测试配置
sudo systemctl restart nginx
```

### 3. 如果后端在 Docker 容器中

如果后端在 Docker 容器中（通过 docker-compose），并且 Ubuntu 服务器上有 Nginx 代理到容器：

1. 修改 Ubuntu 服务器的 Nginx 配置（如上）
2. 重新构建并重启 Docker 容器：

```bash
cd /path/to/HIS_interface
docker-compose build --no-cache backend
docker-compose restart backend
```

### 4. 如果后端直接运行（不在 Docker 中）

如果后端直接运行在 Ubuntu 服务器上（如 `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`），并且有 Nginx 反向代理：

- 修改 Nginx 配置（如上）
- 重启 Nginx

### 5. 如果后端没有 Nginx（直接访问）

如果后端直接暴露 8000 端口，没有 Nginx：

- Uvicorn 本身不限制文件大小
- 问题可能在前端 Vite 代理
- 检查 Vite 配置（已配置，应该没问题）

## 快速修复（推荐）

在 Ubuntu 服务器上执行以下命令，检查并修复 Nginx 配置：

```bash
# 1. 检查是否有 Nginx
sudo systemctl status nginx

# 2. 如果有 Nginx，检查配置
sudo nginx -t

# 3. 查找所有 Nginx 配置文件
sudo find /etc/nginx -name "*.conf" -exec grep -l "8000\|proxy_pass" {} \;

# 4. 在找到的配置文件中添加或修改：
# client_max_body_size 100M;

# 5. 重启 Nginx
sudo nginx -t
sudo systemctl restart nginx
```

## 验证

修复后，尝试上传文件，应该不再出现 413 错误。

