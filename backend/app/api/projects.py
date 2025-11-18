"""
项目API路由模块

本模块提供项目的RESTful API接口：
1. 创建项目
2. 获取项目列表（支持关键词搜索和分页）
3. 获取项目详情（包含接口和字典统计）
4. 更新项目信息
5. 删除项目
6. 获取项目下的接口列表
7. 获取项目下的字典列表

作者: Auto
创建时间: 2024
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from backend.database import get_db
from backend.app import crud
from backend.app.schemas import (
    ProjectCreate, ProjectUpdate, Project, ProjectDetail, ProjectAttachment
)
from backend.app.utils.file_upload import save_uploaded_file, delete_uploaded_file, get_file_url
from backend.app.api.auth import get_current_user
from backend.app.models import User
from backend.app.utils.permissions import check_project_permission
import json

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _ensure_list(value):
    """将可能为None/str/obj的字段安全转换为list。"""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
    return []


def _normalize_attachments(raw_attachments) -> List[Dict[str, Any]]:
    """
    规范化附件列表
    - 确保 file_url 为相对路径
    - 补充 category/can_preview 字段，兼容旧数据
    """
    normalized = []
    for att in _ensure_list(raw_attachments):
        if not isinstance(att, dict):
            continue

        att_copy = att.copy()
        file_path = att_copy.get("file_path", "")
        stored_file_url = att_copy.get("file_url", "")

        if file_path:
            if stored_file_url and (stored_file_url.startswith("http://") or stored_file_url.startswith("https://")):
                from urllib.parse import urlparse
                parsed = urlparse(stored_file_url)
                att_copy["file_url"] = parsed.path or get_file_url(file_path, base_url=None)
            elif not stored_file_url or not stored_file_url.startswith("/"):
                att_copy["file_url"] = get_file_url(file_path, base_url=None)
            # 如果需要绝对路径，可根据base_url构建，但默认返回相对路径
        else:
            att_copy["file_url"] = stored_file_url

        category = att_copy.get("category") or "pdf"
        att_copy["category"] = category
        if "can_preview" not in att_copy:
            att_copy["can_preview"] = category == "pdf"

        normalized.append(att_copy)
    return normalized

@router.post("", response_model=Project, status_code=201)
def create_project(
    project: ProjectCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建新项目
    
    创建项目时需要提供：
    - 项目名称（必填）
    - 负责人（必填）
    - 联系方式（必填，可存储多个联系方式）
    - 文档列表（可选，JSON格式，每个文档包含：name、version、update_date）
    - 项目功能描述（可选）
    
    权限说明：
    - 所有登录用户都可以创建项目
    - 创建的项目会自动设置创建人为当前登录用户
    
    Args:
        project: 项目创建模型，包含项目基本信息
        db: 数据库会话对象
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        Project: 创建成功的项目对象，包含创建人ID和创建时间
        
    Raises:
        HTTPException 500: 创建项目失败（数据库错误等）
    """
    try:
        # 创建项目，自动设置创建人ID为当前登录用户
        db_project = crud.create_project(db, project, creator_id=current_user.id)
        
        # 手动构建响应对象，避免SQLAlchemy自动加载关联关系
        # 这样可以避免查询不存在的列或循环引用问题
        return Project(
            id=db_project.id,
            name=db_project.name,
            manager=db_project.manager,
            contact_info=db_project.contact_info,
            documents=_ensure_list(db_project.documents),
            attachments=_normalize_attachments(db_project.attachments),
            description=db_project.description,
            creator_id=db_project.creator_id,
            created_at=db_project.created_at,
            updated_at=db_project.updated_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")


@router.get("", response_model=List[Project])
def get_projects(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    keyword: Optional[str] = Query(None, description="关键词（搜索项目名称、负责人、描述）"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目列表
    
    支持关键词搜索和分页。
    关键词会在项目名称、负责人、描述中搜索。
    
    权限规则：
    - 管理员可以看到所有项目
    - 普通用户只能看到：
      * 管理员创建的项目
      * 自己创建的项目
      * 没有创建人的项目（兼容旧数据）
    
    Args:
        skip: 跳过的记录数（用于分页）
        limit: 返回的最大记录数
        keyword: 关键词（可选，用于搜索项目名称、负责人、描述）
        request: HTTP请求对象（用于获取base_url，当前未使用）
        db: 数据库会话对象
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        List[Project]: 项目列表，根据权限过滤后的结果
    """
    # 调用CRUD函数获取项目列表，传入用户ID和角色信息用于权限过滤
    db_projects = crud.get_projects(
        db, 
        skip=skip, 
        limit=limit, 
        keyword=keyword, 
        user_id=current_user.id, 
        is_admin=current_user.role.value == 'admin'
    )
    # 手动构建响应对象列表，避免SQLAlchemy自动加载关联关系
    # 这样可以避免查询不存在的列或循环引用问题
    projects = []
    for p in db_projects:
        # 规范化附件列表，确保file_url为相对路径
        # 前端会根据当前域名自动构建完整的URL
        attachments = _normalize_attachments(p.attachments)
        
        # 构建项目响应对象
        projects.append(Project(
            id=p.id,
            name=p.name,
            manager=p.manager,
            contact_info=p.contact_info,
            documents=_ensure_list(p.documents),
            attachments=attachments,
            description=p.description,
            creator_id=p.creator_id,
            created_at=p.created_at,
            updated_at=p.updated_at
        ))
    return projects


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(
    project_id: int, 
    request: Request = None, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取项目详情
    
    返回项目详细信息，包括：
    - 项目基本信息
    - 接口数量统计
    - 字典数量统计
    
    权限规则：
    - 管理员可以看到所有项目
    - 普通用户只能看到：
      * 管理员创建的项目
      * 自己创建的项目
      * 没有创建人的项目（兼容旧数据）
    
    Args:
        project_id: 项目ID
        request: HTTP请求对象（当前未使用）
        db: 数据库会话对象
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        ProjectDetail: 项目详情对象，包含基本信息和统计信息
        
    Raises:
        HTTPException 404: 项目不存在
        HTTPException 403: 无权访问此项目
    """
    # 获取项目信息，不加载关联关系以避免查询不存在的列
    db_project = crud.get_project(db, project_id, load_relations=False)
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查：普通用户只能访问管理员创建的项目和自己创建的项目
    if current_user.role.value != 'admin':
        from backend.app.models import User, UserRole
        # 如果项目有创建人，需要检查权限
        if db_project.creator_id is not None:
            # 获取创建人信息，检查创建人是否是管理员
            creator = db.query(User).filter(User.id == db_project.creator_id).first()
            # 如果创建人不是管理员也不是当前用户，则拒绝访问
            if creator and creator.role != UserRole.ADMIN and db_project.creator_id != current_user.id:
                raise HTTPException(status_code=403, detail="无权访问此项目")
    
    # 直接查询数据库获取接口和字典数量（避免通过关联关系查询）
    # 使用try-except处理可能的列不存在的情况（兼容旧数据库结构）
    from backend.app.models import Interface, Dictionary
    try:
        interfaces_count = db.query(Interface).filter(Interface.project_id == project_id).count()
    except Exception:
        # 如果project_id列不存在（旧数据库结构），返回0
        interfaces_count = 0
    
    try:
        dictionaries_count = db.query(Dictionary).filter(Dictionary.project_id == project_id).count()
    except Exception:
        # 如果project_id列不存在（旧数据库结构），返回0
        dictionaries_count = 0
    
    # 规范化附件列表，确保file_url为相对路径
    # 前端会根据当前域名自动构建完整的URL
    attachments = _normalize_attachments(db_project.attachments)
    
    # 构建项目详情响应对象
    # 注意：不包含interfaces和dictionaries的详细信息，只包含数量统计
    # 这样可以避免循环引用和性能问题
    from backend.app.schemas import ProjectDetail
    project_detail = ProjectDetail(
        id=db_project.id,
        name=db_project.name,
        manager=db_project.manager,
        contact_info=db_project.contact_info,
        documents=_ensure_list(db_project.documents),
        attachments=attachments,
        description=db_project.description,
        creator_id=db_project.creator_id,
        interfaces_count=interfaces_count,
        dictionaries_count=dictionaries_count,
        created_at=db_project.created_at,
        updated_at=db_project.updated_at,
        interfaces=[],  # 不包含详细信息，避免循环引用
        dictionaries=[]  # 不包含详细信息，避免循环引用
    )
    
    return project_detail


@router.put("/{project_id}", response_model=Project)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新项目信息
    
    支持部分更新，只更新请求体中提供的字段，未提供的字段保持不变。
    
    权限规则：
    - 管理员可以更新所有项目
    - 普通用户只能更新自己创建的项目（创建人是user类型的）
    - 普通用户不能更新管理员创建的项目
    
    Args:
        project_id: 要更新的项目ID
        project_update: 项目更新模型（所有字段都是可选的）
        db: 数据库会话对象
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        Project: 更新后的项目对象
        
    Raises:
        HTTPException 404: 项目不存在
        HTTPException 403: 无权操作此项目
    """
    # 获取项目信息
    db_project = crud.get_project(db, project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查权限：使用权限检查函数验证用户是否有权限更新此项目
    if not check_project_permission(db_project.creator_id, current_user):
        raise HTTPException(status_code=403, detail="无权操作此项目")
    
    # 执行更新操作
    db_project = crud.update_project(db, project_id, project_update)
    
    # 手动构建响应对象，避免SQLAlchemy自动加载关联关系
    return Project(
        id=db_project.id,
        name=db_project.name,
        manager=db_project.manager,
        contact_info=db_project.contact_info,
        documents=_ensure_list(db_project.documents),
        attachments=_normalize_attachments(db_project.attachments),
        description=db_project.description,
        creator_id=db_project.creator_id,
        created_at=db_project.created_at,
        updated_at=db_project.updated_at
    )


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除项目
    
    删除项目时会级联删除所有关联的接口和字典。
    注意：此操作不可恢复，请谨慎操作！
    
    权限规则：
    - 管理员可以删除所有项目
    - 普通用户只能删除自己创建的项目（创建人是user类型的）
    - 普通用户不能删除管理员创建的项目
    
    Args:
        project_id: 要删除的项目ID
        db: 数据库会话对象
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        None: 删除成功返回204状态码
        
    Raises:
        HTTPException 404: 项目不存在
        HTTPException 403: 无权操作此项目
    """
    # 获取项目信息
    db_project = crud.get_project(db, project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 检查权限：使用权限检查函数验证用户是否有权限删除此项目
    if not check_project_permission(db_project.creator_id, current_user):
        raise HTTPException(status_code=403, detail="无权操作此项目")
    
    # 执行删除操作（会级联删除关联的接口和字典）
    success = crud.delete_project(db, project_id)
    if not success:
        raise HTTPException(status_code=404, detail="项目不存在")
    return None


@router.get("/{project_id}/interfaces", response_model=List[dict])
def get_project_interfaces(
    project_id: int,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    db: Session = Depends(get_db)
):
    """
    获取项目下的接口列表
    
    返回指定项目下的所有接口。
    """
    # 验证项目是否存在（不加载关联关系）
    db_project = crud.get_project(db, project_id, load_relations=False)
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 直接查询数据库获取接口（避免通过关联关系查询）
    from backend.app.models import Interface as InterfaceModel
    interfaces = db.query(InterfaceModel).filter(
        InterfaceModel.project_id == project_id
    ).offset(skip).limit(limit).all()
    
    # 转换为字典列表
    result = []
    for interface in interfaces:
        interface_dict = {
            "id": interface.id,
            "name": interface.name,
            "code": interface.code,
            "description": interface.description,
            "interface_type": interface.interface_type.value if interface.interface_type else None,
            "url": interface.url,
            "method": interface.method,
            "status": interface.status,
            "created_at": interface.created_at,
            "updated_at": interface.updated_at
        }
        result.append(interface_dict)
    
    return result


@router.get("/{project_id}/dictionaries", response_model=List[dict])
def get_project_dictionaries(
    project_id: int,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    db: Session = Depends(get_db)
):
    """
    获取项目下的字典列表
    
    返回指定项目下的所有字典。
    """
    # 验证项目是否存在（不加载关联关系）
    db_project = crud.get_project(db, project_id, load_relations=False)
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 直接查询数据库获取字典（避免通过关联关系查询）
    from backend.app.models import Dictionary as DictionaryModel
    dictionaries = db.query(DictionaryModel).filter(
        DictionaryModel.project_id == project_id
    ).offset(skip).limit(limit).all()
    
    # 转换为字典列表
    result = []
    for dictionary in dictionaries:
        dictionary_dict = {
            "id": dictionary.id,
            "name": dictionary.name,
            "code": dictionary.code,
            "description": dictionary.description,
            "created_at": dictionary.created_at,
            "updated_at": dictionary.updated_at,
            "values_count": len(dictionary.values) if dictionary.values else 0
        }
        result.append(dictionary_dict)
    
    return result


@router.post("/{project_id}/attachments", response_model=ProjectAttachment)
def upload_project_attachment(
    project_id: int,
    file: UploadFile = File(...),
    category: str = Query("pdf", description="附件类别：pdf（可预览）或 other（仅下载）"),
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传项目附件
    
    支持两种附件类别：
    - pdf: 仅支持PDF文件，上传后可在线预览
    - other: 允许任意常见格式，仅支持下载查看
    
    单个文件最大50MB，上传成功后文件信息会保存到项目的 attachments 字段中（JSON格式）。
    
    权限规则：
    - 管理员可以向所有项目上传附件
    - 普通用户只能向自己创建的项目上传附件（创建人是user类型的）
    - 普通用户不能向管理员创建的项目上传附件
    
    Args:
        project_id: 项目ID
        file: 上传的文件对象
        category: 附件类别（pdf或other）
        request: HTTP请求对象（当前未使用）
        db: 数据库会话对象
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        ProjectAttachment: 上传成功的附件信息对象
        
    Raises:
        HTTPException 404: 项目不存在
        HTTPException 403: 无权向此项目上传附件
        HTTPException 400: 附件类别无效
    """
    # 验证项目是否存在
    db_project = crud.get_project(db, project_id, load_relations=False)
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查：普通用户只能向自己创建的项目上传附件
    if current_user.role.value != 'admin':
        from backend.app.models import User, UserRole
        # 如果项目有创建人，需要检查权限
        if db_project.creator_id is not None:
            # 获取创建人信息
            creator = db.query(User).filter(User.id == db_project.creator_id).first()
            if creator:
                # 如果创建人是admin，普通用户不能上传
                if creator.role == UserRole.ADMIN:
                    raise HTTPException(status_code=403, detail="无权向此项目上传附件")
                # 如果创建人是user，只有创建人自己可以上传
                elif creator.role == UserRole.USER and db_project.creator_id != current_user.id:
                    raise HTTPException(status_code=403, detail="无权向此项目上传附件")
    
    # 验证附件类别
    if category not in {"pdf", "other"}:
        raise HTTPException(status_code=400, detail="附件类别必须是 pdf 或 other")
    
    # 保存文件到服务器
    file_info = save_uploaded_file(file, project_id, category=category)
    
    # 构建文件URL（使用相对路径）
    # 不保存绝对路径，避免端口号错误或域名变更问题
    # 前端会根据当前域名自动构建完整的URL
    relative_url = get_file_url(file_info["file_path"], base_url=None)
    
    # 确保URL是相对路径格式（不以http://或https://开头）
    if relative_url.startswith("http://") or relative_url.startswith("https://"):
        # 如果返回的是绝对路径，提取相对路径部分
        from urllib.parse import urlparse
        parsed = urlparse(relative_url)
        relative_url = parsed.path
    
    # 确保路径以/开头
    if not relative_url.startswith("/"):
        relative_url = f"/{relative_url}"
    
    file_info["file_url"] = relative_url
    
    # 更新项目的附件列表（JSON格式存储）
    attachments = _ensure_list(db_project.attachments)
    
    # 创建附件信息对象，用于保存到数据库
    # 确保file_url是相对路径，避免端口号或域名变更问题
    file_info_for_db = {
        "filename": file_info["filename"],
        "stored_filename": file_info["stored_filename"],
        "file_path": file_info["file_path"],
        "file_size": file_info["file_size"],
        "upload_time": file_info["upload_time"],
        "file_url": relative_url,  # 使用相对路径
        "category": file_info.get("category", category),
        "can_preview": file_info.get("can_preview", category == "pdf")
    }
    attachments.append(file_info_for_db)
    
    # 更新数据库：手动JSON序列化，避免不同后端的JSON类型兼容问题
    # ensure_ascii=False 确保中文字符正确保存
    from backend.app.models import Project as ProjectModel
    db.query(ProjectModel).filter(ProjectModel.id == project_id).update({
        "attachments": json.dumps(attachments, ensure_ascii=False)
    })
    db.commit()
    
    # 返回附件信息给前端
    # 注意：ProjectAttachment schema 不包含 file_url 字段，所以不会返回URL
    return ProjectAttachment(**file_info)


@router.delete("/{project_id}/attachments/{stored_filename}")
def delete_project_attachment(
    project_id: int,
    stored_filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除项目附件
    
    从项目的 attachments 列表中移除指定文件，并删除服务器上的物理文件。
    
    权限规则：
    - 管理员可以删除所有项目的附件
    - 普通用户只能删除自己创建的项目的附件（创建人是user类型的）
    - 普通用户不能删除管理员创建的项目附件
    
    Args:
        project_id: 项目ID
        stored_filename: 存储的文件名（带时间戳的文件名）
        db: 数据库会话对象
        current_user: 当前登录用户（通过Token验证）
        
    Returns:
        dict: 删除成功消息
        
    Raises:
        HTTPException 404: 项目不存在或附件不存在
        HTTPException 403: 无权删除此项目的附件
    """
    # 验证项目是否存在
    db_project = crud.get_project(db, project_id, load_relations=False)
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 权限检查：普通用户只能删除自己创建的项目的附件
    if current_user.role.value != 'admin':
        from backend.app.models import User, UserRole
        # 如果项目有创建人，需要检查权限
        if db_project.creator_id is not None:
            # 获取创建人信息
            creator = db.query(User).filter(User.id == db_project.creator_id).first()
            if creator:
                # 如果创建人是admin，普通用户不能删除
                if creator.role == UserRole.ADMIN:
                    raise HTTPException(status_code=403, detail="无权删除此项目的附件")
                # 如果创建人是user，只有创建人自己可以删除
                elif creator.role == UserRole.USER and db_project.creator_id != current_user.id:
                    raise HTTPException(status_code=403, detail="无权删除此项目的附件")
    
    # 获取附件列表
    attachments = _ensure_list(db_project.attachments)
    
    # 查找要删除的附件（根据存储的文件名匹配）
    attachment_to_delete = None
    for att in attachments:
        if att.get("stored_filename") == stored_filename:
            attachment_to_delete = att
            break
    
    if not attachment_to_delete:
        raise HTTPException(status_code=404, detail="附件不存在")
    
    # 删除服务器上的物理文件
    file_path = attachment_to_delete.get("file_path")
    if file_path:
        delete_uploaded_file(file_path)
    
    # 从附件列表中移除
    attachments.remove(attachment_to_delete)
    
    # 更新数据库：手动JSON序列化，避免不同后端的JSON类型兼容问题
    # ensure_ascii=False 确保中文字符正确保存
    from backend.app.models import Project as ProjectModel
    db.query(ProjectModel).filter(ProjectModel.id == project_id).update({
        "attachments": json.dumps(attachments, ensure_ascii=False) if attachments else None
    })
    db.commit()
    
    return {"message": "附件删除成功"}

