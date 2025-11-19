"""
常见问题API路由模块

本模块提供常见问题的RESTful API接口：
1. 创建常见问题（支持文件上传）
2. 获取常见问题列表（支持关键词搜索和分页）
3. 获取常见问题详情
4. 更新常见问题信息
5. 删除常见问题（同时删除文件）

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
    FAQCreate, FAQUpdate, FAQ, FAQSearch, FAQListResponse
)
from backend.app.utils.document_upload import (
    save_uploaded_file, delete_uploaded_file, move_file_to_faq_dir
)
from backend.app.models import DocumentType, ContentType, FAQ as FAQModel
from backend.app.api.auth import get_current_user
from backend.app.models import User
from backend.app.utils.permissions import check_resource_permission

router = APIRouter(prefix="/api/faqs", tags=["常见问题"])


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


def _build_faq_response(db_faq: FAQModel) -> FAQ:
    """构建常见问题响应对象，处理向后兼容"""
    # 处理attachments
    attachments = _ensure_list(db_faq.attachments)
    
    # 向后兼容：如果attachments为空但file_path存在，转换为attachments格式
    if not attachments and db_faq.file_path:
        attachments = [{
            "filename": db_faq.file_name or "未知文件",
            "stored_filename": db_faq.file_path.split("/")[-1] if db_faq.file_path else "",
            "file_path": _normalize_file_path(db_faq.file_path) or "",
            "file_size": db_faq.file_size or 0,
            "mime_type": db_faq.mime_type,
            "upload_time": db_faq.created_at.isoformat() if db_faq.created_at else ""
        }]
    
    return FAQ(
        id=db_faq.id,
        title=db_faq.title,
        description=db_faq.description,
        module=db_faq.module,
        person=db_faq.person,
        document_type=db_faq.document_type,
        content_type=getattr(db_faq, "content_type", ContentType.ATTACHMENT),
        rich_content=getattr(db_faq, "rich_content", None),
        file_path=_normalize_file_path(db_faq.file_path) if db_faq.file_path else None,
        file_name=db_faq.file_name,
        file_size=db_faq.file_size,
        mime_type=db_faq.mime_type,
        attachments=attachments,
        creator_id=getattr(db_faq, "creator_id", None),
        created_at=db_faq.created_at,
        updated_at=db_faq.updated_at
    )


@router.post("", response_model=FAQ, status_code=201)
def create_faq(
    title: str = Form(..., description="标题"),
    description: Optional[str] = Form(None, description="简要描述"),
    module: Optional[str] = Form(None, max_length=50, description="模块"),
    person: Optional[str] = Form(None, max_length=50, description="人员"),
    document_type: str = Form(..., description="文档类型（向后兼容字段）"),
    content_type: Optional[str] = Form(ContentType.ATTACHMENT.value, description="内容类型：attachment（附件类型，PDF附件）或rich_text（富文本类型）"),
    rich_content: Optional[str] = Form(None, description="富文本内容，HTML格式，仅在content_type为rich_text时使用"),
    files: Optional[List[UploadFile]] = File(None, description="上传的文件（仅attachment类型需要，只支持PDF）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新常见问题
    
    支持两种内容类型：
    1. attachment（附件类型）：必须上传PDF文件，不支持图片
    2. rich_text（富文本类型）：使用富文本编辑器编辑图文混排内容，不需要上传文件
    
    权限说明：
    - 所有登录用户都可以创建常见问题
    - 创建的常见问题会自动设置创建人为当前登录用户
    
    Args:
        title: 常见问题标题（必填）
        description: 简要描述（可选）
        module: 模块（可选，最大50字符）
        person: 人员（可选，最大50字符）
        document_type: 文档类型（必填，向后兼容字段，必须是'pdf'）
        content_type: 内容类型（可选，默认'attachment'，必须是'attachment'或'rich_text'）
        rich_content: 富文本内容（可选，仅在content_type为'rich_text'时使用）
        files: 上传的文件对象列表（可选，仅在content_type为'attachment'时必填，只支持PDF格式）
        db: 数据库会话对象（自动注入）
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        FAQ: 创建成功的常见问题对象，包含文件信息或富文本内容
        
    Raises:
        HTTPException 400: 内容类型无效、文件列表为空或文件格式不正确
        HTTPException 500: 文件保存失败
    """
    # 验证内容类型
    try:
        content_type_enum = ContentType(content_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"无效的内容类型：{content_type}，必须是 'attachment' 或 'rich_text'"
        )
    
    # 验证文档类型（向后兼容，新数据统一使用pdf）
    try:
        doc_type = DocumentType(document_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"无效的文档类型：{document_type}，必须是 'pdf' 或 'image'"
        )
    
    # 根据内容类型进行不同的处理
    if content_type_enum == ContentType.RICH_TEXT:
        # 富文本类型：不需要文件，只需要富文本内容
        if not rich_content or not rich_content.strip():
            raise HTTPException(
                status_code=400,
                detail="富文本类型必须提供富文本内容"
            )
        
        # 创建常见问题记录（富文本类型）
        faq_data = FAQCreate(
            title=title,
            description=description,
            module=module,
            person=person,
            document_type=DocumentType.PDF,  # 向后兼容，统一使用pdf
            content_type=content_type_enum,
            rich_content=rich_content
        )
        
        db_faq = crud.create_faq(db, faq_data, creator_id=current_user.id)
        db.commit()
        db.refresh(db_faq)
        
        return _build_faq_response(db_faq)
    
    else:
        # 附件类型：必须上传PDF文件
        if not files or len(files) == 0:
            raise HTTPException(
                status_code=400,
                detail="附件类型必须上传至少一个PDF文件"
            )
        
        # 验证所有文件都是PDF格式
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail=f"附件类型只支持PDF文件，不支持文件：{file.filename}"
                )
        
        # PDF类型只允许上传一个文件
        if len(files) > 1:
            raise HTTPException(
                status_code=400,
                detail="附件类型只允许上传一个PDF文件"
            )
        
        # 处理PDF文件上传
        file = files[0]  # 只处理第一个文件（附件类型只允许一个）
        file_info = save_uploaded_file(file, DocumentType.PDF.value)
        
        # 创建常见问题记录
        faq_data = FAQCreate(
            title=title,
            description=description,
            module=module,
            person=person,
            document_type=DocumentType.PDF,  # 向后兼容，统一使用pdf
            content_type=content_type_enum,
            rich_content=None
        )
        
        db_faq = crud.create_faq(
            db=db,
            faq=faq_data,
            file_path=file_info["file_path"],
            file_name=file_info["filename"],
            file_size=file_info["file_size"],
            mime_type=file_info["mime_type"],
            creator_id=current_user.id
        )
        
        # 将文件移动到常见问题目录
        new_file_path = move_file_to_faq_dir(file_info["file_path"], db_faq.id)
        
        # 构建附件信息
        attachment_info = {
            "filename": file_info["filename"],
            "stored_filename": file_info["stored_filename"],
            "file_path": new_file_path,
            "file_size": file_info["file_size"],
            "mime_type": file_info["mime_type"],
            "upload_time": file_info["upload_time"]
        }
        
        # 更新数据库：保存attachments和file_path（向后兼容）
        db_faq.file_path = new_file_path
        db.query(FAQModel).filter(FAQModel.id == db_faq.id).update({
            "attachments": json.dumps([attachment_info], ensure_ascii=False)
        })
        db.commit()
        db.refresh(db_faq)
        
        return _build_faq_response(db_faq)


@router.get("", response_model=FAQListResponse)
def get_faqs(
    keyword: Optional[str] = Query(None, description="关键词（搜索标题、简要描述）"),
    document_type: Optional[DocumentType] = Query(None, description="文档类型"),
    module: Optional[str] = Query(None, description="模块"),
    person: Optional[str] = Query(None, description="人员"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取常见问题列表（支持多条件筛选、关键词搜索和分页）
    
    支持以下筛选条件：
    - 关键词搜索：在标题、简要描述中模糊匹配
    - 文档类型筛选：pdf或image
    - 模块筛选：按模块精确匹配
    - 人员筛选：按人员精确匹配
    
    权限规则：
    - 管理员可以看到所有常见问题
    - 普通用户只能看到：
      * 管理员创建的常见问题
      * 自己创建的常见问题
      * 没有创建人的常见问题（兼容旧数据）
    
    Args:
        keyword: 关键词（可选，用于在标题、简要描述中搜索）
        document_type: 文档类型（可选，pdf或image）
        module: 模块（可选，精确匹配）
        person: 人员（可选，精确匹配）
        page: 页码（默认1，最小1）
        page_size: 每页数量（默认20，最小1，最大100）
        db: 数据库会话对象（自动注入）
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        FAQListResponse: 包含总数、页码、每页数量和常见问题列表的响应对象
    """
    search = FAQSearch(
        keyword=keyword,
        document_type=document_type,
        module=module,
        person=person,
        page=page,
        page_size=page_size
    )
    
    items, total = crud.search_faqs(
        db, 
        search, 
        user_id=current_user.id, 
        is_admin=current_user.role.value == 'admin'
    )
    
    # 转换为响应模型
    faq_list = []
    for item in items:
        faq_list.append(_build_faq_response(item))
    
    return FAQListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=faq_list
    )


@router.get("/{faq_id}", response_model=FAQ)
def get_faq(faq_id: int, db: Session = Depends(get_db)):
    """
    根据ID获取常见问题详情
    
    返回常见问题的完整信息，包括：
    - 常见问题基本信息（标题、描述、模块、人员等）
    - 文件信息（路径、文件名、大小、MIME类型等）
    - 创建时间和更新时间
    
    Args:
        faq_id: 常见问题ID（路径参数）
        db: 数据库会话对象（自动注入）
        
    Returns:
        FAQ: 常见问题对象，包含所有常见问题信息和文件元数据
        
    Raises:
        HTTPException 404: 常见问题不存在
    """
    db_faq = crud.get_faq(db, faq_id)
    if not db_faq:
        raise HTTPException(status_code=404, detail="常见问题不存在")
    
    return _build_faq_response(db_faq)


@router.put("/{faq_id}", response_model=FAQ)
def update_faq(
    faq_id: int,
    faq_update: FAQUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新常见问题信息（部分更新）
    
    支持部分更新，只更新请求体中提供的字段，未提供的字段保持不变。
    注意：此接口不支持更新文件，如需更新文件请删除后重新创建。
    
    权限规则：
    - 管理员可以更新所有常见问题
    - 普通用户只能更新自己创建的常见问题（创建人是user类型的）
    - 普通用户不能更新管理员创建的常见问题
    
    Args:
        faq_id: 要更新的常见问题ID（路径参数）
        faq_update: 常见问题更新模型（所有字段都是可选的）
        db: 数据库会话对象（自动注入）
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        FAQ: 更新后的常见问题对象
        
    Raises:
        HTTPException 404: 常见问题不存在
        HTTPException 403: 无权操作此常见问题
    """
    # 先获取常见问题，检查权限
    db_faq = crud.get_faq(db, faq_id)
    if not db_faq:
        raise HTTPException(status_code=404, detail="常见问题不存在")
    
    # 检查权限
    if not check_resource_permission(db_faq.creator_id, current_user, db, allow_read=False):
        raise HTTPException(status_code=403, detail="无权操作此常见问题")
    
    db_faq = crud.update_faq(db, faq_id, faq_update)
    if not db_faq:
        raise HTTPException(status_code=404, detail="常见问题不存在")
    
    return _build_faq_response(db_faq)


@router.delete("/{faq_id}", status_code=204)
def delete_faq(
    faq_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除常见问题（同时删除文件）
    
    删除常见问题时会同时删除服务器上的物理文件。
    注意：此操作不可恢复，请谨慎使用。
    
    权限规则：
    - 管理员可以删除所有常见问题
    - 普通用户只能删除自己创建的常见问题（创建人是user类型的）
    - 普通用户不能删除管理员创建的常见问题
    
    Args:
        faq_id: 要删除的常见问题ID（路径参数）
        db: 数据库会话对象（自动注入）
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        None: 删除成功返回204状态码
        
    Raises:
        HTTPException 404: 常见问题不存在
        HTTPException 403: 无权操作此常见问题
    """
    # 先获取常见问题信息，以便删除文件
    db_faq = crud.get_faq(db, faq_id)
    if not db_faq:
        raise HTTPException(status_code=404, detail="常见问题不存在")
    
    # 检查权限
    if not check_resource_permission(db_faq.creator_id, current_user, db, allow_read=False):
        raise HTTPException(status_code=403, detail="无权操作此常见问题")
    
    # 删除所有附件文件
    attachments = _ensure_list(db_faq.attachments)
    if attachments:
        # 删除attachments中的所有文件
        for attachment in attachments:
            if attachment.get("file_path"):
                delete_uploaded_file(attachment["file_path"])
    elif db_faq.file_path:
        # 向后兼容：删除旧格式的文件
        delete_uploaded_file(db_faq.file_path)
    
    # 删除数据库记录
    success = crud.delete_faq(db, faq_id)
    if not success:
        raise HTTPException(status_code=404, detail="常见问题不存在")
    
    return None


@router.post("/{faq_id}/attachments", response_model=FAQ)
def add_faq_attachment(
    faq_id: int,
    file: UploadFile = File(..., description="上传的文件"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    为常见问题添加附件
    
    权限规则：
    - 管理员可以为所有常见问题添加附件
    - 普通用户只能为自己创建的常见问题添加附件
    
    Args:
        faq_id: 常见问题ID
        file: 上传的文件对象
        db: 数据库会话对象
        current_user: 当前登录用户
        
    Returns:
        FAQ: 更新后的常见问题对象
    """
    db_faq = crud.get_faq(db, faq_id)
    if not db_faq:
        raise HTTPException(status_code=404, detail="常见问题不存在")
    
    # 检查权限
    if not check_resource_permission(db_faq.creator_id, current_user, db, allow_read=False):
        raise HTTPException(status_code=403, detail="无权操作此常见问题")
    
    # 验证文件类型（根据文档类型）
    doc_type = db_faq.document_type.value
    file_info = save_uploaded_file(file, doc_type)
    
    # 将文件移动到常见问题目录
    new_file_path = move_file_to_faq_dir(file_info["file_path"], faq_id)
    
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
    attachments = _ensure_list(db_faq.attachments)
    attachments.append(attachment_info)
    
    # 更新数据库
    db.query(FAQModel).filter(FAQModel.id == faq_id).update({
        "attachments": json.dumps(attachments, ensure_ascii=False)
    })
    db.commit()
    db.refresh(db_faq)
    
    return _build_faq_response(db_faq)


@router.delete("/{faq_id}/attachments/{stored_filename}", response_model=FAQ)
def delete_faq_attachment(
    faq_id: int,
    stored_filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除常见问题的指定附件
    
    权限规则：
    - 管理员可以删除所有常见问题的附件
    - 普通用户只能删除自己创建的常见问题的附件
    
    Args:
        faq_id: 常见问题ID
        stored_filename: 存储的文件名（带时间戳）
        db: 数据库会话对象
        current_user: 当前登录用户
        
    Returns:
        FAQ: 更新后的常见问题对象
    """
    db_faq = crud.get_faq(db, faq_id)
    if not db_faq:
        raise HTTPException(status_code=404, detail="常见问题不存在")
    
    # 检查权限
    if not check_resource_permission(db_faq.creator_id, current_user, db, allow_read=False):
        raise HTTPException(status_code=403, detail="无权操作此常见问题")
    
    # 获取attachments列表
    attachments = _ensure_list(db_faq.attachments)
    
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
    db.query(FAQModel).filter(FAQModel.id == faq_id).update({
        "attachments": json.dumps(attachments, ensure_ascii=False) if attachments else None
    })
    db.commit()
    db.refresh(db_faq)
    
    return _build_faq_response(db_faq)

