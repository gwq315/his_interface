#!/bin/bash
# Docker 快速部署脚本

set -e

echo "=========================================="
echo "HIS 接口文档管理系统 - Docker 部署脚本"
echo "=========================================="
echo ""

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 Docker Compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 检查配置文件是否存在
if [ ! -f "backend/config.ini" ]; then
    echo "警告: backend/config.ini 不存在"
    echo "正在从模板创建配置文件..."
    if [ -f "backend/config.ini.example" ]; then
        cp backend/config.ini.example backend/config.ini
        echo "✓ 已创建 backend/config.ini"
        echo ""
        echo "请编辑 backend/config.ini 文件，配置数据库连接信息："
        echo "  - server: Windows 主机的 IP 地址"
        echo "  - port: 1433"
        echo "  - database: HIS_Interface"
        echo "  - username: SQL Server 用户名"
        echo "  - password: SQL Server 密码"
        echo ""
        read -p "按 Enter 键继续（确保已配置好数据库连接）..."
    else
        echo "错误: backend/config.ini.example 不存在"
        exit 1
    fi
fi

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p uploads/projects
echo "✓ 目录创建完成"

# 构建镜像
echo ""
echo "构建 Docker 镜像..."
docker-compose build

# 启动服务
echo ""
echo "启动服务..."
docker-compose up -d

# 等待服务启动
echo ""
echo "等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "检查服务状态..."
docker-compose ps

# 检查健康状态
echo ""
echo "检查后端健康状态..."
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✓ 后端服务运行正常"
else
    echo "⚠ 后端服务可能未正常启动，请查看日志: docker-compose logs backend"
fi

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  前端: http://localhost"
echo "  后端 API: http://localhost:8000"
echo "  API 文档: http://localhost:8000/docs"
echo ""
echo "常用命令："
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  查看状态: docker-compose ps"
echo ""

