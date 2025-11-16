"""
文档/截图上传工具模块

提供文档和截图上传、删除等功能。
支持PDF文档和图片（PNG、JPEG、JPG、GIF、WEBP等）。

作者: Auto
创建时间: 2024
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException
import mimetypes


# 上传目录基础路径（相对于项目根目录）
UPLOAD_BASE_DIR = "uploads"
DOCUMENT_UPLOAD_DIR = "uploads/documents"

# 允许的文件类型
ALLOWED_PDF_EXTENSIONS = {".pdf"}
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

# 最大文件大小（50MB）
MAX_FILE_SIZE = 50 * 1024 * 1024


def ensure_upload_dir(document_id: Optional[int] = None) -> Path:
    """
    确保文档上传目录存在
    
    Args:
        document_id: 文档ID（如果提供，创建子目录）
        
    Returns:
        Path: 文档上传目录路径
    """
    project_root = Path(__file__).parent.parent.parent.parent
    if document_id:
        upload_dir = project_root / DOCUMENT_UPLOAD_DIR / str(document_id)
    else:
        upload_dir = project_root / DOCUMENT_UPLOAD_DIR
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def validate_file(file: UploadFile, document_type: str) -> None:
    """
    验证上传文件
    
    Args:
        file: 上传的文件对象
        document_type: 文档类型（"pdf" 或 "image"）
        
    Raises:
        HTTPException: 文件验证失败
    """
    # 检查文件扩展名
    file_ext = Path(file.filename).suffix.lower()
    
    if document_type == "pdf":
        if file_ext not in ALLOWED_PDF_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。仅支持PDF文件（.pdf）"
            )
    elif document_type == "image":
        if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。仅支持图片文件（.png, .jpg, .jpeg, .gif, .webp, .bmp）"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文档类型：{document_type}"
        )
    
    # 检查文件大小（需要在读取后检查，这里先检查Content-Length）
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制（最大50MB）"
        )


def save_uploaded_file(file: UploadFile, document_type: str, document_id: Optional[int] = None) -> Dict[str, Any]:
    """
    保存上传的文件
    
    Args:
        file: 上传的文件对象
        document_type: 文档类型（"pdf" 或 "image"）
        document_id: 文档ID（如果提供，保存到子目录）
        
    Returns:
        Dict: 包含文件信息的字典
            - filename: 原始文件名
            - stored_filename: 存储的文件名
            - file_path: 文件相对路径
            - file_size: 文件大小（字节）
            - mime_type: MIME类型
            - upload_time: 上传时间（ISO格式）
            
    Raises:
        HTTPException: 文件保存失败
    """
    # 验证文件
    validate_file(file, document_type)
    
    # 确保上传目录存在
    upload_dir = ensure_upload_dir(document_id)
    
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
        
        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(original_filename)
        if not mime_type:
            # 根据扩展名设置默认MIME类型
            if file_ext == ".pdf":
                mime_type = "application/pdf"
            elif file_ext in {".png"}:
                mime_type = "image/png"
            elif file_ext in {".jpg", ".jpeg"}:
                mime_type = "image/jpeg"
            elif file_ext == ".gif":
                mime_type = "image/gif"
            elif file_ext == ".webp":
                mime_type = "image/webp"
            elif file_ext == ".bmp":
                mime_type = "image/bmp"
        
        # 构建文件信息
        if document_id:
            file_path_str = f"{DOCUMENT_UPLOAD_DIR}/{document_id}/{stored_filename}"
        else:
            # 临时保存，稍后移动到正确位置
            file_path_str = f"{DOCUMENT_UPLOAD_DIR}/{stored_filename}"
        
        file_info = {
            "filename": original_filename,
            "stored_filename": stored_filename,
            "file_path": file_path_str,
            "file_size": file_size,
            "mime_type": mime_type,
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


def save_image_from_bytes(image_data: bytes, filename: str, document_id: Optional[int] = None) -> Dict[str, Any]:
    """
    从字节数据保存图片（用于剪贴板粘贴）
    
    Args:
        image_data: 图片的字节数据
        filename: 文件名（建议包含扩展名）
        document_id: 文档ID（如果提供，保存到子目录）
        
    Returns:
        Dict: 包含文件信息的字典
        
    Raises:
        HTTPException: 文件保存失败
    """
    # 检查文件大小
    file_size = len(image_data)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制（最大50MB）"
        )
    
    # 确保上传目录存在
    upload_dir = ensure_upload_dir(document_id)
    
    # 生成存储文件名
    timestamp = int(datetime.now().timestamp())
    file_ext = Path(filename).suffix.lower()
    if not file_ext:
        # 如果没有扩展名，默认使用PNG
        file_ext = ".png"
        filename = f"{filename}.png"
    stored_filename = f"{timestamp}_{filename}"
    
    # 完整文件路径
    file_path = upload_dir / stored_filename
    
    try:
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(image_data)
        
        # 获取MIME类型
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            if file_ext == ".png":
                mime_type = "image/png"
            elif file_ext in {".jpg", ".jpeg"}:
                mime_type = "image/jpeg"
            elif file_ext == ".gif":
                mime_type = "image/gif"
            elif file_ext == ".webp":
                mime_type = "image/webp"
            elif file_ext == ".bmp":
                mime_type = "image/bmp"
            else:
                mime_type = "image/png"  # 默认
        
        # 构建文件信息
        if document_id:
            file_path_str = f"{DOCUMENT_UPLOAD_DIR}/{document_id}/{stored_filename}"
        else:
            file_path_str = f"{DOCUMENT_UPLOAD_DIR}/{stored_filename}"
        
        file_info = {
            "filename": filename,
            "stored_filename": stored_filename,
            "file_path": file_path_str,
            "file_size": file_size,
            "mime_type": mime_type,
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


def move_file_to_document_dir(file_path: str, document_id: int) -> str:
    """
    将临时文件移动到文档目录
    
    Args:
        file_path: 临时文件路径
        document_id: 文档ID
        
    Returns:
        str: 新的文件相对路径
    """
    project_root = Path(__file__).parent.parent.parent.parent
    old_path = project_root / file_path
    
    if not old_path.exists():
        return file_path
    
    # 确保目标目录存在
    target_dir = ensure_upload_dir(document_id)
    
    # 移动文件
    new_path = target_dir / old_path.name
    old_path.rename(new_path)
    
    # 返回新的相对路径
    return f"{DOCUMENT_UPLOAD_DIR}/{document_id}/{old_path.name}"


def delete_uploaded_file(file_path: str) -> bool:
    """
    删除上传的文件
    
    Args:
        file_path: 文件相对路径（如：uploads/documents/1/1704067200_文档.pdf）
        
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


def get_file_url(file_path: str, base_url: str = "http://localhost:8000") -> str:
    """
    获取文件的访问URL
    
    Args:
        file_path: 文件相对路径
        base_url: 基础URL（默认localhost:8000）
        
    Returns:
        str: 文件的完整访问URL
    """
    # 将Windows路径转换为URL路径
    url_path = file_path.replace("\\", "/")
    return f"{base_url}/{url_path}"

