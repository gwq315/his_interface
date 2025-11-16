"""
文件上传工具模块

提供项目附件上传、删除等功能。

作者: Auto
创建时间: 2024
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException
import json


# 上传目录基础路径（相对于项目根目录）
UPLOAD_BASE_DIR = "uploads"
PROJECT_UPLOAD_DIR = "uploads/projects"

# 允许的文件类型
ALLOWED_EXTENSIONS = {".pdf"}

# 最大文件大小（50MB）
MAX_FILE_SIZE = 50 * 1024 * 1024


def ensure_upload_dir(project_id: int) -> Path:
    """
    确保项目上传目录存在
    
    Args:
        project_id: 项目ID
        
    Returns:
        Path: 项目上传目录路径
    """
    project_root = Path(__file__).parent.parent.parent.parent
    upload_dir = project_root / PROJECT_UPLOAD_DIR / str(project_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def validate_file(file: UploadFile) -> None:
    """
    验证上传文件
    
    Args:
        file: 上传的文件对象
        
    Raises:
        HTTPException: 文件验证失败
    """
    # 检查文件扩展名
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。仅支持PDF文件（.pdf）"
        )
    
    # 检查文件大小（需要在读取后检查，这里先检查Content-Length）
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制（最大50MB）"
        )


def save_uploaded_file(file: UploadFile, project_id: int) -> Dict[str, Any]:
    """
    保存上传的文件
    
    Args:
        file: 上传的文件对象
        project_id: 项目ID
        
    Returns:
        Dict: 包含文件信息的字典
            - filename: 原始文件名
            - stored_filename: 存储的文件名
            - file_path: 文件相对路径
            - file_size: 文件大小（字节）
            - upload_time: 上传时间（ISO格式）
            
    Raises:
        HTTPException: 文件保存失败
    """
    # 验证文件
    validate_file(file)
    
    # 确保上传目录存在
    upload_dir = ensure_upload_dir(project_id)
    
    # 生成存储文件名（时间戳 + 原始文件名）
    timestamp = int(datetime.now().timestamp())
    original_filename = file.filename
    file_ext = Path(original_filename).suffix
    stored_filename = f"{timestamp}_{original_filename}"
    
    # 完整文件路径
    file_path = upload_dir / stored_filename
    
    try:
        # 读取文件内容并保存
        file_content = file.file.read()
        file_size = len(file_content)
        
        # 检查文件大小
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制（最大50MB）"
            )
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # 构建文件信息
        file_info = {
            "filename": original_filename,
            "stored_filename": stored_filename,
            "file_path": f"{PROJECT_UPLOAD_DIR}/{project_id}/{stored_filename}",
            "file_size": file_size,
            "upload_time": datetime.now().isoformat()
        }
        
        return file_info
        
    except Exception as e:
        # 如果保存失败，删除可能已创建的文件
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"文件保存失败: {str(e)}"
        )


def delete_uploaded_file(file_path: str) -> bool:
    """
    删除上传的文件
    
    Args:
        file_path: 文件相对路径（如：uploads/projects/1/1704067200_文档.pdf）
        
    Returns:
        bool: 是否删除成功
    """
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        full_path = project_root / file_path
        
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    except Exception as e:
        print(f"删除文件失败: {str(e)}")
        return False


def get_file_url(file_path: str, base_url: str = None) -> str:
    """
    获取文件的访问URL
    
    Args:
        file_path: 文件相对路径
        base_url: 基础URL（如果为None，则返回相对路径；如果提供，则返回绝对URL）
        
    Returns:
        str: 文件的访问URL（相对路径或绝对URL）
        
    说明：
    - 保存到数据库时，应使用相对路径（base_url=None），不检查环境变量
    - 返回给前端时，应使用绝对URL（base_url=当前请求的base_url）
    """
    # 将Windows路径转换为URL路径
    url_path = file_path.replace("\\", "/")
    
    # 确保路径以/开头
    if not url_path.startswith("/"):
        url_path = f"/{url_path}"
    
    # 如果提供了base_url，返回绝对URL
    if base_url:
        # 移除base_url末尾的斜杠
        base_url = base_url.rstrip("/")
        return f"{base_url}{url_path}"
    
    # 如果没有提供base_url，返回相对路径（前端会基于当前域名构建完整URL）
    # 保存到数据库时使用相对路径，避免端口号错误或域名变更问题
    # 注意：不检查环境变量，确保保存时始终使用相对路径
    return url_path

