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

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import FileResponse
import sys
from pathlib import Path
import mimetypes
import os

# 增加 FormData 的大小限制（1000MB）
# 通过 monkey patch 修改 starlette.formparsers.MultiPartParser 的默认 max_part_size
try:
    from starlette.formparsers import MultiPartParser
    import inspect
    
    # 保存原始的 __init__ 方法
    _original_init = MultiPartParser.__init__
    
    # 获取原始方法的签名
    sig = inspect.signature(_original_init)
    params = list(sig.parameters.keys())
    
    def _patched_init(self, *args, **kwargs):
        # 如果 max_part_size 未指定，使用 100MB 作为默认值
        if 'max_part_size' not in kwargs:
            kwargs['max_part_size'] = 1000 * 1024 * 1024  # 100MB
        elif kwargs.get('max_part_size') is None:
            kwargs['max_part_size'] = 1000 * 1024 * 1024  # 100MB
        
        return _original_init(self, *args, **kwargs)
    
    # 应用 monkey patch
    MultiPartParser.__init__ = _patched_init
    print("已成功应用 FormData 大小限制 patch（1000MB）")
except Exception as e:
    # 如果导入或 patch 失败，记录警告但继续运行
    print(f"警告: FormData 大小限制 patch 失败: {e}")
    pass

# ========== 路径配置 ==========

# 添加项目根目录到Python路径，确保可以正确导入模块
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# ========== 导入模块 ==========

from backend.database import init_db
from backend.app.api import projects, interfaces, parameters, dictionaries, import_export, documents, faqs, auth
from backend.app.utils.init_faq_module_dict import init_faq_module_dictionary

# ========== 数据库初始化 ==========

# 延迟初始化数据库，避免启动时阻塞
# 首次请求时再初始化数据库连接和表结构
# 这样可以更快启动服务，即使数据库暂时不可用也能启动
try:
    init_db()
    print("数据库初始化成功")
    
    # 初始化常见问题模块字典
    try:
        init_faq_module_dictionary()
    except Exception as e:
        print(f"警告: 常见问题模块字典初始化失败: {e}")
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
app.include_router(auth.router)           # 用户认证路由
app.include_router(projects.router)        # 项目管理路由
app.include_router(interfaces.router)     # 接口管理路由
app.include_router(parameters.router)     # 参数管理路由
app.include_router(dictionaries.router)   # 字典管理路由
app.include_router(import_export.router)  # 导入导出路由
app.include_router(documents.router)      # 文档/截图管理路由
app.include_router(faqs.router)            # 常见问题路由

# ========== 静态文件服务 ==========

# 配置静态文件服务，用于访问上传的附件
# 上传目录：uploads/
# 访问URL：http://localhost:8000/uploads/projects/{project_id}/{filename}
uploads_dir = project_root / "uploads"
uploads_dir.mkdir(exist_ok=True)

# 自定义静态文件路由，确保图片文件返回正确的Content-Type
@app.get("/uploads/{file_path:path}")
@app.head("/uploads/{file_path:path}")  # 支持 HEAD 请求（用于 curl -I）
async def serve_uploaded_file(file_path: str, request: Request = None):
    """
    提供上传文件的访问服务，确保图片文件返回正确的Content-Type
    
    这个路由优先于StaticFiles挂载，确保图片文件能正确显示
    """
    # 构建完整文件路径
    # FastAPI会自动解码URL编码的路径参数，所以file_path已经是解码后的
    # 但为了安全，我们需要确保路径是相对路径
    if file_path.startswith('/'):
        file_path = file_path[1:]  # 移除开头的斜杠
    
    full_path = uploads_dir / file_path
    
    # 安全检查：确保文件在uploads目录内（防止路径遍历攻击）
    try:
        full_path = full_path.resolve()
        uploads_dir_resolved = uploads_dir.resolve()
        if not str(full_path).startswith(str(uploads_dir_resolved)):
            raise HTTPException(status_code=403, detail="访问被拒绝")
    except (ValueError, OSError):
        raise HTTPException(status_code=403, detail="无效的文件路径")
    
    # 检查文件是否存在
    if not full_path.exists() or not full_path.is_file():
        # 生产环境：提供更详细的错误信息用于调试
        error_detail = f"文件不存在: {file_path}"
        # 可选：在生产环境记录更详细的日志（可以通过环境变量控制）
        import os
        if os.getenv("DEBUG", "false").lower() == "true":
            print(f"[文件服务] 文件不存在: {full_path}")
            print(f"[文件服务] 目录是否存在: {full_path.parent.exists()}")
            if full_path.parent.exists():
                print(f"[文件服务] 目录内容: {list(full_path.parent.iterdir())}")
        raise HTTPException(status_code=404, detail=error_detail)
    
    # 获取MIME类型
    mime_type, _ = mimetypes.guess_type(str(full_path))
    
    # 对于图片文件，确保返回正确的MIME类型
    if not mime_type:
        ext = full_path.suffix.lower()
        if ext == ".png":
            mime_type = "image/png"
        elif ext in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"
        elif ext == ".gif":
            mime_type = "image/gif"
        elif ext == ".webp":
            mime_type = "image/webp"
        elif ext == ".bmp":
            mime_type = "image/bmp"
        elif ext == ".pdf":
            mime_type = "application/pdf"
        else:
            mime_type = "application/octet-stream"
    
    # 返回文件，确保设置正确的Content-Type
    return FileResponse(
        path=str(full_path),
        media_type=mime_type,
        headers={
            "Cache-Control": "public, max-age=3600"  # 缓存1小时
        }
    )

# 注意：我们使用自定义路由而不是StaticFiles挂载
# 这样可以确保图片文件返回正确的Content-Type，并且有更好的错误处理

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

