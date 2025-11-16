# 代理配置验证指南

本文档提供详细的步骤来验证 nginx 和 Vite 的代理配置是否正确。

## 一、配置检查清单

### 1.1 Nginx 配置检查（生产环境）

**配置文件位置：** `nginx.conf`

**关键配置项：**

```nginx
# ✅ 检查点 1: /api 代理配置
location /api {
    proxy_pass http://backend:8000;  # 必须指向后端服务名和端口
    # ... 其他配置
}

# ✅ 检查点 2: /uploads 代理配置
location /uploads {
    proxy_pass http://backend:8000;  # 必须指向后端服务名和端口
    # ... 其他配置
}
```

**重要说明：`backend` 的含义**

- **`backend`** 是 **Docker Compose 服务名**，必须与 `docker-compose.yml` 中定义的服务名一致
- 这是 **Docker 网络内部的主机名**，不是宿主机 IP 地址
- **端口 8000** 是后端容器**内部端口**，不是宿主机映射端口
- 如果修改了 `docker-compose.yml` 中的服务名（例如改为 `api-server`），nginx.conf 中的 `backend` 也需要相应修改为 `api-server`

**工作原理：**
1. Docker Compose 会自动创建一个内部网络（`his-network`）
2. 服务名 `backend` 会自动注册为网络中的主机名
3. 前端容器（nginx）通过服务名 `backend` 访问后端容器
4. 这是容器间通信的标准方式，不需要知道容器的实际 IP 地址

**验证要点：**
- [ ] `proxy_pass` 中的服务名必须与 `docker-compose.yml` 中的服务名一致（当前是 `backend`）
- [ ] 端口必须是后端容器内部端口（当前是 `8000`），不是宿主机映射端口
- [ ] 没有多余的斜杠（`proxy_pass http://backend:8000/` 会导致路径被重写）
- [ ] `client_max_body_size` 设置足够大（至少 100M）
- [ ] 配置已正确复制到 Docker 容器中
- [ ] 前端和后端容器都在同一个 Docker 网络中（检查 `docker-compose.yml` 中的 `networks` 配置）

### 1.2 Vite 配置检查（开发环境）

**配置文件位置：** `frontend/vite.config.js`

**关键配置项：**

```javascript
proxy: {
  '/api': {
    target: apiBaseUrl,  // 默认: 'http://localhost:8000'
    changeOrigin: true,
    secure: false
  },
  '/uploads': {
    target: apiBaseUrl,  // 默认: 'http://localhost:8000'
    changeOrigin: true,
    secure: false
  }
}
```

**验证要点：**
- [ ] `target` 指向正确的后端地址
- [ ] 如果后端在远程服务器，检查 `.env` 文件中的 `VITE_API_BASE_URL`
- [ ] `changeOrigin: true` 已设置（处理跨域）

## 二、验证方法

### 2.1 开发环境验证（Vite）

#### 步骤 1: 检查后端服务
```bash
# 检查后端是否运行在 8000 端口
curl http://localhost:8000/health
# 应该返回: {"status":"ok"}
```

#### 步骤 2: 启动前端开发服务器
```bash
cd frontend
npm run dev
```

#### 步骤 3: 测试 API 代理
在浏览器控制台或使用 curl：
```bash
# 测试 API 代理
curl http://localhost:5173/api/projects
# 应该返回项目列表的 JSON 数据
```

#### 步骤 4: 测试文件代理
```bash
# 测试 /uploads 代理（替换为实际的文件路径）
curl -I http://localhost:5173/uploads/documents/8/1763202578_xxx.png
# 应该返回 200 OK 和正确的 Content-Type
```

#### 步骤 5: 检查浏览器网络请求
1. 打开浏览器开发者工具（F12）
2. 切换到 "Network" 标签
3. 刷新页面，查看请求
4. 检查 `/api` 和 `/uploads` 请求：
   - **Status**: 应该是 200（成功）或 404（文件不存在，但代理工作正常）
   - **Response Headers**: 应该包含后端返回的头部信息

### 2.2 生产环境验证（Nginx + Docker）

#### 步骤 1: 检查容器状态
```bash
# 检查所有容器是否运行
docker-compose ps

# 应该看到：
# - his-interface-backend (运行中)
# - his-interface-frontend (运行中)
```

#### 步骤 2: 检查网络连接
```bash
# 进入前端容器
docker exec -it his-interface-frontend sh

# 在容器内测试后端连接
wget -O- http://backend:8000/health
# 或使用 curl（如果容器内有）
curl http://backend:8000/health
# 应该返回: {"status":"ok"}
```

#### 步骤 3: 检查 Nginx 配置
```bash
# 进入前端容器
docker exec -it his-interface-frontend sh

# 检查 nginx 配置语法
nginx -t
# 应该显示: syntax is ok, test is successful

# 查看实际加载的配置
cat /etc/nginx/conf.d/default.conf
```

#### 步骤 4: 测试 API 代理
```bash
# 从宿主机测试（假设前端映射到 5173 端口）
curl http://localhost:5173/api/projects
# 或从外部访问
curl http://192.168.1.198:5173/api/projects
```

#### 步骤 5: 测试文件代理
```bash
# 测试文件访问（替换为实际路径）
curl -I http://192.168.1.198:5173/uploads/documents/8/1763202578_xxx.png

# 检查响应头：
# - HTTP/1.1 200 OK
# - Content-Type: image/png (或其他正确的 MIME 类型)
```

#### 步骤 6: 查看 Nginx 日志
```bash
# 查看访问日志
docker logs his-interface-frontend

# 或实时查看
docker logs -f his-interface-frontend

# 查看错误日志（如果有）
docker exec -it his-interface-frontend tail -f /var/log/nginx/error.log
```

## 三、常见问题排查

### 问题 1: 404 Not Found

**症状：** 访问 `/uploads/...` 返回 404

**排查步骤：**
1. 检查文件是否存在于后端容器中：
   ```bash
   docker exec -it his-interface-backend ls -la /app/uploads/documents/8/
   ```

2. 检查后端路由是否正常：
   ```bash
   # 直接访问后端
   curl http://192.168.1.198:8000/uploads/documents/8/1763202578_xxx.png
   ```

3. 检查 nginx 代理配置：
   ```bash
   # 查看 nginx 配置中的 proxy_pass 是否正确
   docker exec -it his-interface-frontend cat /etc/nginx/conf.d/default.conf | grep -A 5 "location /uploads"
   ```

### 问题 2: 502 Bad Gateway

**症状：** 访问代理路径返回 502

**排查步骤：**
1. 检查后端服务是否运行：
   ```bash
   docker ps | grep backend
   docker logs his-interface-backend
   ```

2. 检查网络连接：
   ```bash
   # 从前端容器测试后端连接
   docker exec -it his-interface-frontend ping backend
   docker exec -it his-interface-frontend wget -O- http://backend:8000/health
   ```

3. 检查 Docker 网络：
   ```bash
   docker network inspect his-interface_his-network
   # 确认 backend 和 frontend 都在同一个网络中
   ```

### 问题 3: 中文文件名乱码

**症状：** 包含中文的文件名无法访问

**排查步骤：**
1. 检查 URL 编码：
   - 浏览器应该自动编码中文
   - 检查实际请求的 URL 是否正确编码

2. 检查后端日志：
   ```bash
   docker logs his-interface-backend | grep -i "file_path"
   ```

### 问题 4: Content-Type 不正确

**症状：** 图片无法显示，但文件存在

**排查步骤：**
1. 检查响应头：
   ```bash
   curl -I http://192.168.1.198:5173/uploads/documents/8/xxx.png
   # 应该看到: Content-Type: image/png
   ```

2. 检查后端是否正确设置 Content-Type：
   ```bash
   # 直接访问后端
   curl -I http://192.168.1.198:8000/uploads/documents/8/xxx.png
   ```

## 四、快速验证脚本

创建一个验证脚本 `verify_proxy.sh` 来自动检查：

```bash
#!/bin/bash

echo "=== 代理配置验证 ==="

# 检查后端健康状态
echo "1. 检查后端服务..."
BACKEND_HEALTH=$(curl -s http://localhost:8000/health)
if [ "$BACKEND_HEALTH" == '{"status":"ok"}' ]; then
    echo "   ✅ 后端服务正常"
else
    echo "   ❌ 后端服务异常: $BACKEND_HEALTH"
fi

# 检查 API 代理（开发环境）
if curl -s http://localhost:5173/api/projects > /dev/null 2>&1; then
    echo "   ✅ Vite API 代理正常"
else
    echo "   ⚠️  Vite API 代理可能有问题（开发环境）"
fi

# 检查 Docker 容器
echo "2. 检查 Docker 容器..."
if docker ps | grep -q his-interface-backend; then
    echo "   ✅ 后端容器运行中"
else
    echo "   ❌ 后端容器未运行"
fi

if docker ps | grep -q his-interface-frontend; then
    echo "   ✅ 前端容器运行中"
    
    # 检查 nginx 配置
    if docker exec his-interface-frontend nginx -t > /dev/null 2>&1; then
        echo "   ✅ Nginx 配置正确"
    else
        echo "   ❌ Nginx 配置有误"
    fi
else
    echo "   ❌ 前端容器未运行"
fi

echo "=== 验证完成 ==="
```

## 五、调试技巧

### 5.1 启用详细日志

**Nginx 调试：**
在 `nginx.conf` 中添加：
```nginx
error_log /var/log/nginx/error.log debug;
access_log /var/log/nginx/access.log;
```

**Vite 调试：**
启动时添加 `--debug` 参数：
```bash
npm run dev -- --debug
```

### 5.2 使用浏览器开发者工具

1. **Network 标签：**
   - 查看请求 URL
   - 查看请求/响应头
   - 查看响应内容

2. **Console 标签：**
   - 查看 JavaScript 错误
   - 查看 API 调用日志

### 5.3 使用 curl 测试

```bash
# 详细输出
curl -v http://192.168.1.198:5173/api/projects

# 只查看响应头
curl -I http://192.168.1.198:5173/uploads/documents/8/xxx.png

# 跟随重定向
curl -L http://192.168.1.198:5173/api/projects
```

## 六、常见配置问题解答

### Q1: `http://backend:8000` 中的 `backend` 是固定的吗？

**答：** `backend` 是 **Docker Compose 服务名**，必须与 `docker-compose.yml` 中的服务名一致。

- ✅ **正确做法：** 保持 `backend` 不变（如果 docker-compose.yml 中服务名是 `backend`）
- ❌ **错误做法：** 改为宿主机 IP（如 `http://192.168.1.198:8000`）
- ❌ **错误做法：** 改为容器名（如 `http://his-interface-backend:8000`）

**原因：**
- Docker Compose 会自动将服务名注册为网络主机名
- 容器间通信使用服务名，不需要知道实际 IP
- 即使容器重启，服务名保持不变，IP 可能变化

### Q2: 什么时候需要修改 `backend`？

**需要修改的情况：**
1. 修改了 `docker-compose.yml` 中的服务名：
   ```yaml
   services:
     api-server:  # 如果改为 api-server
       ...
   ```
   那么 nginx.conf 中也要改为：
   ```nginx
   proxy_pass http://api-server:8000;
   ```

2. 使用不同的 Docker Compose 文件，服务名不同

**不需要修改的情况：**
1. 修改了宿主机 IP 地址（容器间通信不受影响）
2. 修改了宿主机端口映射（如 `8000:8000` 改为 `9000:8000`）
3. 修改了容器名（`container_name`）

### Q3: 端口 8000 可以修改吗？

**答：** 可以，但需要同时修改两个地方：

1. **后端容器内部端口**（如果修改了后端应用监听的端口）：
   ```yaml
   # docker-compose.yml
   services:
     backend:
       ports:
         - "8000:9000"  # 宿主机:容器内部
   ```
   ```nginx
   # nginx.conf
   proxy_pass http://backend:9000;  # 使用容器内部端口
   ```

2. **宿主机映射端口**（只影响外部访问，不影响容器间通信）：
   ```yaml
   services:
     backend:
       ports:
         - "9000:8000"  # 宿主机端口改为 9000，容器内部仍是 8000
   ```
   ```nginx
   # nginx.conf 不需要修改，仍使用容器内部端口
   proxy_pass http://backend:8000;
   ```

### Q4: 如何验证服务名是否正确？

```bash
# 进入前端容器
docker exec -it his-interface-frontend sh

# 测试服务名解析
ping backend
# 或
wget -O- http://backend:8000/health

# 查看 Docker 网络中的服务
docker network inspect his-interface_his-network
```

## 七、配置对比表

| 配置项 | 开发环境 (Vite) | 生产环境 (Nginx) |
|--------|----------------|-----------------|
| 前端端口 | 5173 | 80 (容器内) / 5173 (宿主机) |
| 后端地址 | localhost:8000 | backend:8000 (Docker 网络服务名) |
| API 代理 | `/api` → `http://localhost:8000/api` | `/api` → `http://backend:8000/api` |
| 文件代理 | `/uploads` → `http://localhost:8000/uploads` | `/uploads` → `http://backend:8000/uploads` |
| 配置文件 | `vite.config.js` | `nginx.conf` |
| **关键区别** | 使用 `localhost`（宿主机） | 使用 `backend`（Docker 服务名） |

## 八、验证清单

完成以下检查后，代理配置应该正常工作：

- [ ] 后端服务正常运行（`/health` 返回 ok）
- [ ] 前端服务正常运行
- [ ] API 请求能正常代理（返回数据而非 404/502）
- [ ] 文件请求能正常代理（返回文件或正确的 404）
- [ ] 中文文件名能正常访问
- [ ] 图片能正确显示（Content-Type 正确）
- [ ] 大文件上传正常（不超过 100M）

