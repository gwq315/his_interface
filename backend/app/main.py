"""
FastAPI应用入口模块

本模块是应用的入口点，负责：
1. 初始化FastAPI应用
2. 配置CORS中间件（允许前端跨域访问）
3. 注册所有API路由
4. 初始化数据库

启动方式：
- 开发环境：uvicorn backend.app.main:app --reload --port 8000
- 生产环境：使用Gunicorn或类似WSGI服务器

作者: Auto
创建时间: 2024
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
import sys
from pathlib import Path

# ========== 路径配置 ==========

# 添加项目根目录到Python路径，确保可以正确导入模块
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# ========== 导入模块 ==========

from backend.database import init_db
from backend.app.api import projects, interfaces, parameters, dictionaries, import_export, documents

# ========== 数据库初始化 ==========

# 延迟初始化数据库，避免启动时阻塞
# 首次请求时再初始化数据库连接和表结构
# 这样可以更快启动服务，即使数据库暂时不可用也能启动
try:
    init_db()
    print("数据库初始化成功")
except Exception as e:
    print(f"警告: 数据库初始化失败，将在首次请求时重试: {e}")

# ========== FastAPI应用创建 ==========

# 创建FastAPI应用实例
app = FastAPI(
    title="医院HIS系统接口文档管理系统",  # API文档标题
    description="用于管理医院HIS系统接口文档的API服务",  # API文档描述
    version="1.0.0"  # API版本号
)

# ========== 字符集中间件 ==========

class CharsetMiddleware(BaseHTTPMiddleware):
    """确保API响应使用UTF-8编码，解决中文乱码问题"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # 为JSON响应添加UTF-8字符集
        if response.headers.get("content-type", "").startswith("application/json"):
            response.headers["content-type"] = "application/json; charset=utf-8"
        return response

app.add_middleware(CharsetMiddleware)

# ========== CORS中间件配置 ==========

# 配置跨域资源共享（CORS）
# 允许前端应用（可能运行在不同端口）访问后端API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（开发环境）
    # 生产环境应限制为具体域名，例如：allow_origins=["https://yourdomain.com"]
    allow_credentials=True,  # 允许携带凭证（如Cookie）
    allow_methods=["*"],  # 允许所有HTTP方法（GET, POST, PUT, DELETE等）
    allow_headers=["*"],  # 允许所有请求头
)

# ========== 路由注册 ==========

# 注册所有API路由模块
app.include_router(projects.router)        # 项目管理路由
app.include_router(interfaces.router)     # 接口管理路由
app.include_router(parameters.router)     # 参数管理路由
app.include_router(dictionaries.router)   # 字典管理路由
app.include_router(import_export.router)  # 导入导出路由
app.include_router(documents.router)      # 文档/截图管理路由

# ========== 静态文件服务 ==========

# 配置静态文件服务，用于访问上传的附件
# 上传目录：uploads/
# 访问URL：http://localhost:8000/uploads/projects/{project_id}/{filename}
uploads_dir = project_root / "uploads"
uploads_dir.mkdir(exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# ========== 根路径和健康检查 ==========

@app.get("/")
def root():
    """
    根路径
    
    返回API的基本信息和文档链接。
    
    Returns:
        dict: 包含API信息和文档链接的字典
    """
    return {
        "message": "医院HIS系统接口文档管理系统API",
        "docs": "/docs",  # Swagger UI文档地址
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    """
    健康检查端点
    
    用于监控服务是否正常运行。
    常用于负载均衡器、监控系统等的健康检查。
    
    Returns:
        dict: 包含状态信息的字典
    """
    return {"status": "ok"}


# ========== 应用启动 ==========

if __name__ == "__main__":
    # 直接运行此文件时启动开发服务器
    import uvicorn
    # host="0.0.0.0" 表示监听所有网络接口
    # port=8000 指定端口号
    uvicorn.run(app, host="0.0.0.0", port=8000)

