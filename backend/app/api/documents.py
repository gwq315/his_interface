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
from typing import Optional
from datetime import datetime
import base64
from backend.database import get_db
from backend.app import crud
from backend.app.schemas import (
    DocumentCreate, DocumentUpdate, Document, DocumentSearch, DocumentListResponse
)
from backend.app.utils.document_upload import (
    save_uploaded_file, save_image_from_bytes, delete_uploaded_file, move_file_to_document_dir
)
from backend.app.models import DocumentType

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("", response_model=Document, status_code=201)
def create_document(
    title: str = Form(..., description="标题"),
    description: Optional[str] = Form(None, description="简要描述"),
    region: Optional[str] = Form(None, max_length=50, description="地区"),
    person: Optional[str] = Form(None, max_length=50, description="人员"),
    document_type: str = Form(..., description="文档类型"),
    file: Optional[UploadFile] = File(None, description="上传的文件"),
    clipboard_data: Optional[str] = Form(None, description="剪贴板数据（base64编码的图片）"),
    db: Session = Depends(get_db)
):
    """
    创建新文档/截图
    
    支持两种方式：
    1. 文件上传：通过file参数上传PDF或图片文件
    2. 剪贴板粘贴：通过clipboard_data参数传递base64编码的图片数据（仅支持图片）
    
    注意：file和clipboard_data二选一，不能同时提供。
    """
    # 验证参数
    if not file and not clipboard_data:
        raise HTTPException(
            status_code=400,
            detail="必须提供文件（file）或剪贴板数据（clipboard_data）"
        )
    
    if file and clipboard_data:
        raise HTTPException(
            status_code=400,
            detail="不能同时提供文件和剪贴板数据"
        )
    
    # 处理文件上传
    if file:
        # 文件上传方式
        # 验证文档类型
        try:
            doc_type = DocumentType(document_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的文档类型：{document_type}，必须是 'pdf' 或 'image'"
            )
        
        file_info = save_uploaded_file(file, doc_type.value)
        
        # 创建文档记录（先保存到临时位置）
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
            mime_type=file_info["mime_type"]
        )
        
        # 将文件移动到文档目录
        new_file_path = move_file_to_document_dir(file_info["file_path"], db_document.id)
        db_document.file_path = new_file_path
        db.commit()
        db.refresh(db_document)
        
        return Document(
            id=db_document.id,
            title=db_document.title,
            description=db_document.description,
            region=db_document.region,
            person=db_document.person,
            document_type=db_document.document_type,
            file_path=db_document.file_path,
            file_name=db_document.file_name,
            file_size=db_document.file_size,
            mime_type=db_document.mime_type,
            created_at=db_document.created_at,
            updated_at=db_document.updated_at
        )
    
    else:
        # 剪贴板粘贴方式（仅支持图片）
        try:
            doc_type = DocumentType(document_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的文档类型：{document_type}，必须是 'pdf' 或 'image'"
            )
        
        if doc_type != DocumentType.IMAGE:
            raise HTTPException(
                status_code=400,
                detail="剪贴板粘贴仅支持图片类型"
            )
        
        try:
            # 解析base64数据
            # 格式可能是：data:image/png;base64,iVBORw0KGgo... 或直接是base64字符串
            if clipboard_data.startswith("data:"):
                # 提取base64部分
                base64_data = clipboard_data.split(",")[1]
            else:
                base64_data = clipboard_data
            
            # 解码base64
            image_data = base64.b64decode(base64_data)
            
            # 生成文件名
            filename = f"clipboard_{int(datetime.now().timestamp())}.png"
            
            # 保存图片
            file_info = save_image_from_bytes(image_data, filename)
            
            # 创建文档记录
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
                mime_type=file_info["mime_type"]
            )
            
            # 将文件移动到文档目录
            new_file_path = move_file_to_document_dir(file_info["file_path"], db_document.id)
            db_document.file_path = new_file_path
            db.commit()
            db.refresh(db_document)
            
            return Document(
                id=db_document.id,
                title=db_document.title,
                description=db_document.description,
                region=db_document.region,
                person=db_document.person,
                document_type=db_document.document_type,
                file_path=db_document.file_path,
                file_name=db_document.file_name,
                file_size=db_document.file_size,
                mime_type=db_document.mime_type,
                created_at=db_document.created_at,
                updated_at=db_document.updated_at
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"解析剪贴板数据失败: {str(e)}"
            )


@router.get("", response_model=DocumentListResponse)
def get_documents(
    keyword: Optional[str] = Query(None, description="关键词（搜索标题、简要描述）"),
    document_type: Optional[DocumentType] = Query(None, description="文档类型"),
    region: Optional[str] = Query(None, description="地区"),
    person: Optional[str] = Query(None, description="人员"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取文档列表（支持关键词搜索和分页）
    
    支持按标题、简要描述进行模糊搜索。
    """
    search = DocumentSearch(
        keyword=keyword,
        document_type=document_type,
        region=region,
        person=person,
        page=page,
        page_size=page_size
    )
    
    items, total = crud.search_documents(db, search)
    
    # 转换为响应模型，确保file_path是相对路径
    document_list = []
    for item in items:
        # 清理file_path，确保是相对路径（不包含http://或https://）
        file_path = item.file_path
        if file_path:
            # 如果file_path是绝对路径，提取相对路径部分
            if file_path.startswith("http://") or file_path.startswith("https://"):
                from urllib.parse import urlparse
                parsed = urlparse(file_path)
                file_path = parsed.path
            # 确保路径以/开头（如果还没有）
            if file_path and not file_path.startswith("/"):
                file_path = f"/{file_path}"
        
        document_list.append(Document(
            id=item.id,
            title=item.title,
            description=item.description,
            region=item.region,
            person=item.person,
            document_type=item.document_type,
            file_path=file_path,
            file_name=item.file_name,
            file_size=item.file_size,
            mime_type=item.mime_type,
            created_at=item.created_at,
            updated_at=item.updated_at
        ))
    
    return DocumentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=document_list
    )


@router.get("/{document_id}", response_model=Document)
def get_document(document_id: int, db: Session = Depends(get_db)):
    """
    获取文档详情
    """
    db_document = crud.get_document(db, document_id)
    if not db_document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 清理file_path，确保是相对路径（不包含http://或https://）
    file_path = db_document.file_path
    if file_path:
        # 如果file_path是绝对路径，提取相对路径部分
        if file_path.startswith("http://") or file_path.startswith("https://"):
            from urllib.parse import urlparse
            parsed = urlparse(file_path)
            file_path = parsed.path
        # 确保路径以/开头（如果还没有）
        if file_path and not file_path.startswith("/"):
            file_path = f"/{file_path}"
    
    return Document(
        id=db_document.id,
        title=db_document.title,
        description=db_document.description,
        region=db_document.region,
        person=db_document.person,
        document_type=db_document.document_type,
        file_path=file_path,
        file_name=db_document.file_name,
        file_size=db_document.file_size,
        mime_type=db_document.mime_type,
        created_at=db_document.created_at,
        updated_at=db_document.updated_at
    )


@router.put("/{document_id}", response_model=Document)
def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    db: Session = Depends(get_db)
):
    """
    更新文档信息
    """
    db_document = crud.update_document(db, document_id, document_update)
    if not db_document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return Document(
        id=db_document.id,
        title=db_document.title,
        description=db_document.description,
        region=db_document.region,
        person=db_document.person,
        document_type=db_document.document_type,
        file_path=db_document.file_path,
        file_name=db_document.file_name,
        file_size=db_document.file_size,
        mime_type=db_document.mime_type,
        created_at=db_document.created_at,
        updated_at=db_document.updated_at
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """
    删除文档（同时删除文件）
    """
    # 先获取文档信息，以便删除文件
    db_document = crud.get_document(db, document_id)
    if not db_document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 删除文件
    delete_uploaded_file(db_document.file_path)
    
    # 删除数据库记录
    success = crud.delete_document(db, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return None

