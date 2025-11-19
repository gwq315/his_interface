"""
文档/截图API路由模块

本模块提供文档和截图的RESTful API接口：
1. 创建文档/截图（支持文件上传和剪贴板粘贴）
2. 获取文档列表（支持关键词搜索和分页）
3. 获取文档详情
4. 更新文档信息
5. 删除文档（同时删除文件）

作者: Auto
创建时间: 2024
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any, Union
import json
from backend.database import get_db
from backend.app import crud
from backend.app.schemas import (
    DocumentCreate, DocumentUpdate, Document, DocumentSearch, DocumentListResponse
)
from backend.app.utils.document_upload import (
    save_uploaded_file, delete_uploaded_file, move_file_to_document_dir
)
from backend.app.models import DocumentType, Document as DocumentModel
from backend.app.api.auth import get_current_user
from backend.app.models import User
from backend.app.utils.permissions import check_resource_permission

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _ensure_list(value) -> List[Dict[str, Any]]:
    """确保值是列表格式"""
    if value is None:
        return []
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return []
    if isinstance(value, list):
        return value
    return []


def _normalize_file_path(file_path: str) -> str:
    """标准化文件路径"""
    if not file_path:
        return None
    # 如果file_path是绝对路径，提取相对路径部分
    if file_path.startswith("http://") or file_path.startswith("https://"):
        from urllib.parse import urlparse
        parsed = urlparse(file_path)
        file_path = parsed.path
    # 确保路径以/开头（如果还没有）
    if file_path and not file_path.startswith("/"):
        file_path = f"/{file_path}"
    return file_path


def _build_document_response(db_document: DocumentModel) -> Document:
    """构建文档响应对象，处理向后兼容"""
    # 处理attachments
    attachments = _ensure_list(db_document.attachments)
    
    # 向后兼容：如果attachments为空但file_path存在，转换为attachments格式
    if not attachments and db_document.file_path:
        attachments = [{
            "filename": db_document.file_name or "未知文件",
            "stored_filename": db_document.file_path.split("/")[-1] if db_document.file_path else "",
            "file_path": _normalize_file_path(db_document.file_path) or "",
            "file_size": db_document.file_size or 0,
            "mime_type": db_document.mime_type,
            "upload_time": db_document.created_at.isoformat() if db_document.created_at else ""
        }]
    
    return Document(
        id=db_document.id,
        title=db_document.title,
        description=db_document.description,
        region=db_document.region,
        person=db_document.person,
        document_type=db_document.document_type,
        file_path=_normalize_file_path(db_document.file_path) if db_document.file_path else None,
        file_name=db_document.file_name,
        file_size=db_document.file_size,
        mime_type=db_document.mime_type,
        attachments=attachments,
        creator_id=getattr(db_document, "creator_id", None),
        created_at=db_document.created_at,
        updated_at=db_document.updated_at
    )


@router.post("", response_model=Document, status_code=201)
def create_document(
    title: str = Form(..., description="标题"),
    description: Optional[str] = Form(None, description="简要描述"),
    region: Optional[str] = Form(None, max_length=50, description="地区"),
    person: Optional[str] = Form(None, max_length=50, description="人员"),
    document_type: str = Form(..., description="文档类型"),
    files: List[UploadFile] = File(..., description="上传的文件（支持多个文件）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新文档/截图
    
    支持上传PDF或图片文件（PNG、JPG、JPEG等）。
    支持一次上传多个文件（图片类型可以上传多个，PDF类型建议只上传一个）。
    文件会先保存到临时目录，创建记录后再移动到文档目录。
    
    权限说明：
    - 所有登录用户都可以创建文档
    - 创建的文档会自动设置创建人为当前登录用户
    
    Args:
        title: 文档标题（必填）
        description: 简要描述（可选）
        region: 地区（可选，最大50字符）
        person: 人员（可选，最大50字符）
        document_type: 文档类型（必填，必须是'pdf'或'image'）
        files: 上传的文件对象列表（必填，至少一个文件，支持PDF或图片格式）
        db: 数据库会话对象（自动注入）
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        Document: 创建成功的文档对象，包含文件信息和元数据
        
    Raises:
        HTTPException 400: 文档类型无效或文件列表为空
        HTTPException 500: 文件保存失败
    """
    # 验证文件列表不为空
    if not files or len(files) == 0:
        raise HTTPException(
            status_code=400,
            detail="至少需要上传一个文件"
        )
    
    # 验证文档类型
    try:
        doc_type = DocumentType(document_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"无效的文档类型：{document_type}，必须是 'pdf' 或 'image'"
        )
    
    # PDF类型建议只上传一个文件
    if doc_type == DocumentType.PDF and len(files) > 1:
        raise HTTPException(
            status_code=400,
            detail="PDF文档类型建议只上传一个文件，如需上传多个请使用图片类型"
        )
    
    # 处理所有上传的文件
    attachments_list = []
    first_file_path = None
    
    for file in files:
        file_info = save_uploaded_file(file, doc_type.value)
        
        # 创建文档记录（只在处理第一个文件时创建）
        if first_file_path is None:
            document_data = DocumentCreate(
                title=title,
                description=description,
                region=region,
                person=person,
                document_type=doc_type
            )
            
            db_document = crud.create_document(
                db=db,
                document=document_data,
                file_path=file_info["file_path"],
                file_name=file_info["filename"],
                file_size=file_info["file_size"],
                mime_type=file_info["mime_type"],
                creator_id=current_user.id
            )
            
            # 将文件移动到文档目录
            new_file_path = move_file_to_document_dir(file_info["file_path"], db_document.id)
            first_file_path = new_file_path
        else:
            # 后续文件直接移动到文档目录
            new_file_path = move_file_to_document_dir(file_info["file_path"], db_document.id)
        
        # 构建附件信息
        attachment_info = {
            "filename": file_info["filename"],
            "stored_filename": file_info["stored_filename"],
            "file_path": new_file_path,
            "file_size": file_info["file_size"],
            "mime_type": file_info["mime_type"],
            "upload_time": file_info["upload_time"]
        }
        attachments_list.append(attachment_info)
    
    # 更新数据库：保存attachments和file_path（向后兼容）
    db_document.file_path = first_file_path
    db.query(DocumentModel).filter(DocumentModel.id == db_document.id).update({
        "attachments": json.dumps(attachments_list, ensure_ascii=False)
    })
    db.commit()
    db.refresh(db_document)
    
    return _build_document_response(db_document)


@router.get("", response_model=DocumentListResponse)
def get_documents(
    keyword: Optional[str] = Query(None, description="关键词（搜索标题、简要描述）"),
    document_type: Optional[DocumentType] = Query(None, description="文档类型"),
    region: Optional[str] = Query(None, description="地区"),
    person: Optional[str] = Query(None, description="人员"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取文档列表（支持多条件筛选、关键词搜索和分页）
    
    支持以下筛选条件：
    - 关键词搜索：在标题、简要描述中模糊匹配
    - 文档类型筛选：pdf或image
    - 地区筛选：按地区精确匹配
    - 人员筛选：按人员精确匹配
    
    权限规则：
    - 管理员可以看到所有文档
    - 普通用户只能看到：
      * 管理员创建的文档
      * 自己创建的文档
      * 没有创建人的文档（兼容旧数据）
    
    Args:
        keyword: 关键词（可选，用于在标题、简要描述中搜索）
        document_type: 文档类型（可选，pdf或image）
        region: 地区（可选，精确匹配）
        person: 人员（可选，精确匹配）
        page: 页码（默认1，最小1）
        page_size: 每页数量（默认20，最小1，最大100）
        db: 数据库会话对象（自动注入）
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        DocumentListResponse: 包含总数、页码、每页数量和文档列表的响应对象
    """
    search = DocumentSearch(
        keyword=keyword,
        document_type=document_type,
        region=region,
        person=person,
        page=page,
        page_size=page_size
    )
    
    items, total = crud.search_documents(
        db, 
        search, 
        user_id=current_user.id, 
        is_admin=current_user.role.value == 'admin'
    )
    
    # 转换为响应模型
    document_list = []
    for item in items:
        document_list.append(_build_document_response(item))
    
    return DocumentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=document_list
    )


@router.get("/{document_id}", response_model=Document)
def get_document(document_id: int, db: Session = Depends(get_db)):
    """
    根据ID获取文档详情
    
    返回文档的完整信息，包括：
    - 文档基本信息（标题、描述、地区、人员等）
    - 文件信息（路径、文件名、大小、MIME类型等）
    - 创建时间和更新时间
    
    Args:
        document_id: 文档ID（路径参数）
        db: 数据库会话对象（自动注入）
        
    Returns:
        Document: 文档对象，包含所有文档信息和文件元数据
        
    Raises:
        HTTPException 404: 文档不存在
    """
    db_document = crud.get_document(db, document_id)
    if not db_document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return _build_document_response(db_document)


@router.put("/{document_id}", response_model=Document)
def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新文档信息（部分更新）
    
    支持部分更新，只更新请求体中提供的字段，未提供的字段保持不变。
    注意：此接口不支持更新文件，如需更新文件请删除后重新创建。
    
    权限规则：
    - 管理员可以更新所有文档
    - 普通用户只能更新自己创建的文档（创建人是user类型的）
    - 普通用户不能更新管理员创建的文档
    
    Args:
        document_id: 要更新的文档ID（路径参数）
        document_update: 文档更新模型（所有字段都是可选的）
        db: 数据库会话对象（自动注入）
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        Document: 更新后的文档对象
        
    Raises:
        HTTPException 404: 文档不存在
        HTTPException 403: 无权操作此文档
    """
    # 先获取文档，检查权限
    db_document = crud.get_document(db, document_id)
    if not db_document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 检查权限
    if not check_resource_permission(db_document.creator_id, current_user, db, allow_read=False):
        raise HTTPException(status_code=403, detail="无权操作此文档")
    
    db_document = crud.update_document(db, document_id, document_update)
    if not db_document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return _build_document_response(db_document)


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除文档（同时删除文件）
    
    删除文档时会同时删除服务器上的物理文件。
    注意：此操作不可恢复，请谨慎使用。
    
    权限规则：
    - 管理员可以删除所有文档
    - 普通用户只能删除自己创建的文档（创建人是user类型的）
    - 普通用户不能删除管理员创建的文档
    
    Args:
        document_id: 要删除的文档ID（路径参数）
        db: 数据库会话对象（自动注入）
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        None: 删除成功返回204状态码
        
    Raises:
        HTTPException 404: 文档不存在
        HTTPException 403: 无权操作此文档
    """
    # 先获取文档信息，以便删除文件
    db_document = crud.get_document(db, document_id)
    if not db_document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 检查权限
    if not check_resource_permission(db_document.creator_id, current_user, db, allow_read=False):
        raise HTTPException(status_code=403, detail="无权操作此文档")
    
    # 删除所有附件文件
    attachments = _ensure_list(db_document.attachments)
    if attachments:
        # 删除attachments中的所有文件
        for attachment in attachments:
            if attachment.get("file_path"):
                delete_uploaded_file(attachment["file_path"])
    elif db_document.file_path:
        # 向后兼容：删除旧格式的文件
        delete_uploaded_file(db_document.file_path)
    
    # 删除数据库记录
    success = crud.delete_document(db, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return None


@router.post("/{document_id}/attachments", response_model=Document)
def add_document_attachment(
    document_id: int,
    file: UploadFile = File(..., description="上传的文件"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    为文档添加附件
    
    权限规则：
    - 管理员可以为所有文档添加附件
    - 普通用户只能为自己创建的文档添加附件
    
    Args:
        document_id: 文档ID
        file: 上传的文件对象
        db: 数据库会话对象
        current_user: 当前登录用户
        
    Returns:
        Document: 更新后的文档对象
    """
    db_document = crud.get_document(db, document_id)
    if not db_document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 检查权限
    if not check_resource_permission(db_document.creator_id, current_user, db, allow_read=False):
        raise HTTPException(status_code=403, detail="无权操作此文档")
    
    # 验证文件类型（根据文档类型）
    doc_type = db_document.document_type.value
    file_info = save_uploaded_file(file, doc_type)
    
    # 将文件移动到文档目录
    new_file_path = move_file_to_document_dir(file_info["file_path"], document_id)
    
    # 构建附件信息
    attachment_info = {
        "filename": file_info["filename"],
        "stored_filename": file_info["stored_filename"],
        "file_path": new_file_path,
        "file_size": file_info["file_size"],
        "mime_type": file_info["mime_type"],
        "upload_time": file_info["upload_time"]
    }
    
    # 更新attachments列表
    attachments = _ensure_list(db_document.attachments)
    attachments.append(attachment_info)
    
    # 更新数据库
    db.query(DocumentModel).filter(DocumentModel.id == document_id).update({
        "attachments": json.dumps(attachments, ensure_ascii=False)
    })
    db.commit()
    db.refresh(db_document)
    
    return _build_document_response(db_document)


@router.delete("/{document_id}/attachments/{stored_filename}", response_model=Document)
def delete_document_attachment(
    document_id: int,
    stored_filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除文档的指定附件
    
    权限规则：
    - 管理员可以删除所有文档的附件
    - 普通用户只能删除自己创建的文档的附件
    
    Args:
        document_id: 文档ID
        stored_filename: 存储的文件名（带时间戳）
        db: 数据库会话对象
        current_user: 当前登录用户
        
    Returns:
        Document: 更新后的文档对象
    """
    db_document = crud.get_document(db, document_id)
    if not db_document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 检查权限
    if not check_resource_permission(db_document.creator_id, current_user, db, allow_read=False):
        raise HTTPException(status_code=403, detail="无权操作此文档")
    
    # 获取attachments列表
    attachments = _ensure_list(db_document.attachments)
    
    # 查找并删除指定附件
    attachment_to_delete = None
    for attachment in attachments:
        if attachment.get("stored_filename") == stored_filename:
            attachment_to_delete = attachment
            break
    
    if not attachment_to_delete:
        raise HTTPException(status_code=404, detail="附件不存在")
    
    # 删除文件
    if attachment_to_delete.get("file_path"):
        delete_uploaded_file(attachment_to_delete["file_path"])
    
    # 从列表中移除
    attachments.remove(attachment_to_delete)
    
    # 更新数据库
    db.query(DocumentModel).filter(DocumentModel.id == document_id).update({
        "attachments": json.dumps(attachments, ensure_ascii=False) if attachments else None
    })
    db.commit()
    db.refresh(db_document)
    
    return _build_document_response(db_document)

