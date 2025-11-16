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
from typing import Optional, List
from backend.database import get_db
from backend.app import crud
from backend.app.schemas import (
    ProjectCreate, ProjectUpdate, Project, ProjectDetail, ProjectAttachment
)
from backend.app.utils.file_upload import save_uploaded_file, delete_uploaded_file, get_file_url
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

@router.post("", response_model=Project, status_code=201)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """
    创建新项目
    
    创建项目时需要提供：
    - 项目名称（必填）
    - 负责人（必填）
    - 联系方式（必填，可存储多个联系方式）
    - 文档列表（可选，JSON格式，每个文档包含：name、version、update_date）
    - 项目功能描述（可选）
    """
    # 检查项目名称是否已存在（可选，如果需要唯一性）
    # 这里暂时不检查，允许同名项目
    
    try:
        db_project = crud.create_project(db, project)
        # 手动构建响应对象，避免SQLAlchemy自动加载关联关系（会查询不存在的project_id列）
        return Project(
            id=db_project.id,
            name=db_project.name,
            manager=db_project.manager,
            contact_info=db_project.contact_info,
            documents=_ensure_list(db_project.documents),
            attachments=_ensure_list(db_project.attachments),
            description=db_project.description,
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
    db: Session = Depends(get_db)
):
    """
    获取项目列表
    
    支持关键词搜索和分页。
    关键词会在项目名称、负责人、描述中搜索。
    """
    # 从请求中获取base_url
    base_url = None
    if request:
        base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    db_projects = crud.get_projects(db, skip=skip, limit=limit, keyword=keyword)
    # 手动构建响应对象列表，避免SQLAlchemy自动加载关联关系
    projects = []
    for p in db_projects:
        # 处理附件，返回时保持相对路径（前端会基于当前域名构建完整URL）
        # 数据库中存储的是相对路径，返回时也保持相对路径，让前端处理
        attachments = _ensure_list(p.attachments)
        for att in attachments:
            if "file_path" in att:
                # 如果存储的是绝对路径（旧数据），提取相对路径部分
                stored_file_url = att.get("file_url", "")
                if stored_file_url and (stored_file_url.startswith("http://") or stored_file_url.startswith("https://")):
                    # 提取相对路径部分
                    from urllib.parse import urlparse
                    parsed = urlparse(stored_file_url)
                    att["file_url"] = parsed.path
                elif not stored_file_url or not stored_file_url.startswith("/"):
                    # 如果没有file_url或不是相对路径，从file_path生成
                    att["file_url"] = get_file_url(att["file_path"], base_url=None)
                # 如果已经是相对路径，保持不变
        
        projects.append(Project(
            id=p.id,
            name=p.name,
            manager=p.manager,
            contact_info=p.contact_info,
            documents=_ensure_list(p.documents),
            attachments=attachments,
            description=p.description,
            created_at=p.created_at,
            updated_at=p.updated_at
        ))
    return projects


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project_id: int, request: Request = None, db: Session = Depends(get_db)):
    """
    获取项目详情
    
    返回项目详细信息，包括：
    - 项目基本信息
    - 接口数量统计
    - 字典数量统计
    """
    # 不加载关联关系，避免查询不存在的列
    db_project = crud.get_project(db, project_id, load_relations=False)
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 直接查询数据库获取数量（避免通过关联关系查询）
    # 如果project_id列不存在，返回0（数据库迁移后会自动更新）
    from backend.app.models import Interface, Dictionary
    try:
        interfaces_count = db.query(Interface).filter(Interface.project_id == project_id).count()
    except Exception:
        # 如果project_id列不存在，返回0
        interfaces_count = 0
    
    try:
        dictionaries_count = db.query(Dictionary).filter(Dictionary.project_id == project_id).count()
    except Exception:
        # 如果project_id列不存在，返回0
        dictionaries_count = 0
    
    # 从请求中获取base_url
    base_url = None
    if request:
        base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    # 处理附件，返回时保持相对路径（前端会基于当前域名构建完整URL）
    # 数据库中存储的是相对路径，返回时也保持相对路径，让前端处理
    attachments = _ensure_list(db_project.attachments)
    for att in attachments:
        if "file_path" in att:
            # 如果存储的是绝对路径（旧数据），提取相对路径部分
            stored_file_url = att.get("file_url", "")
            if stored_file_url and (stored_file_url.startswith("http://") or stored_file_url.startswith("https://")):
                # 提取相对路径部分
                from urllib.parse import urlparse
                parsed = urlparse(stored_file_url)
                att["file_url"] = parsed.path
            elif not stored_file_url or not stored_file_url.startswith("/"):
                # 如果没有file_url或不是相对路径，从file_path生成
                att["file_url"] = get_file_url(att["file_path"], base_url=None)
            # 如果已经是相对路径，保持不变
    
    # 构建响应对象（避免循环引用，不包含interfaces和dictionaries的详细信息）
    from backend.app.schemas import ProjectDetail
    project_detail = ProjectDetail(
        id=db_project.id,
        name=db_project.name,
        manager=db_project.manager,
        contact_info=db_project.contact_info,
        documents=_ensure_list(db_project.documents),
        attachments=attachments,
        description=db_project.description,
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
    db: Session = Depends(get_db)
):
    """
    更新项目信息
    
    支持部分更新，只更新提供的字段。
    """
    db_project = crud.update_project(db, project_id, project_update)
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    # 手动构建响应对象，避免SQLAlchemy自动加载关联关系
    return Project(
        id=db_project.id,
        name=db_project.name,
        manager=db_project.manager,
        contact_info=db_project.contact_info,
        documents=_ensure_list(db_project.documents),
        attachments=_ensure_list(db_project.attachments),
        description=db_project.description,
        created_at=db_project.created_at,
        updated_at=db_project.updated_at
    )


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """
    删除项目
    
    删除项目时会级联删除所有关联的接口和字典。
    请谨慎操作！
    """
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
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    上传项目附件
    
    仅支持PDF格式文件，最大50MB。
    上传成功后，文件信息会保存到项目的 attachments 字段中。
    """
    # 验证项目是否存在
    db_project = crud.get_project(db, project_id, load_relations=False)
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 保存文件
    file_info = save_uploaded_file(file, project_id)
    
    # 保存相对路径到数据库，前端访问时会自动使用当前域名和端口
    # 不保存绝对路径，避免端口号错误或域名变更问题
    # 明确传递 base_url=None，确保返回相对路径
    relative_url = get_file_url(file_info["file_path"], base_url=None)
    
    # 强制确保是相对路径（不以http://或https://开头）
    if relative_url.startswith("http://") or relative_url.startswith("https://"):
        # 如果返回的是绝对路径，提取相对路径部分
        from urllib.parse import urlparse
        parsed = urlparse(relative_url)
        relative_url = parsed.path
    
    # 确保路径以/开头
    if not relative_url.startswith("/"):
        relative_url = f"/{relative_url}"
    
    file_info["file_url"] = relative_url
    # 调试：打印保存的URL（确认是相对路径）
    print(f"保存附件URL到数据库: {relative_url} (应该是相对路径，不以http开头)")
    
    # 更新项目的附件列表
    attachments = _ensure_list(db_project.attachments)
    # 创建用于保存到数据库的副本，确保file_url是相对路径
    file_info_for_db = {
        "filename": file_info["filename"],
        "stored_filename": file_info["stored_filename"],
        "file_path": file_info["file_path"],
        "file_size": file_info["file_size"],
        "upload_time": file_info["upload_time"],
        "file_url": relative_url  # 强制使用相对路径
    }
    attachments.append(file_info_for_db)
    
    # 调试：打印即将保存到数据库的附件信息
    print(f"即将保存到数据库的附件信息: {json.dumps(file_info_for_db, ensure_ascii=False, indent=2)}")
    
    # 使用update并手动json序列化，避免不同后端的JSON类型兼容问题
    # ensure_ascii=False 确保中文字符正确保存
    from backend.app.models import Project as ProjectModel
    db.query(ProjectModel).filter(ProjectModel.id == project_id).update({
        "attachments": json.dumps(attachments, ensure_ascii=False)
    })
    db.commit()
    
    # 返回给前端时，使用相对路径（前端会基于当前域名构建完整URL）
    # ProjectAttachment schema 不包含 file_url 字段，所以不会返回
    return ProjectAttachment(**file_info)


@router.delete("/{project_id}/attachments/{stored_filename}")
def delete_project_attachment(
    project_id: int,
    stored_filename: str,
    db: Session = Depends(get_db)
):
    """
    删除项目附件
    
    从项目的 attachments 列表中移除指定文件，并删除物理文件。
    """
    # 验证项目是否存在
    db_project = crud.get_project(db, project_id, load_relations=False)
    if not db_project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取附件列表
    attachments = _ensure_list(db_project.attachments)
    
    # 查找要删除的附件
    attachment_to_delete = None
    for att in attachments:
        if att.get("stored_filename") == stored_filename:
            attachment_to_delete = att
            break
    
    if not attachment_to_delete:
        raise HTTPException(status_code=404, detail="附件不存在")
    
    # 删除物理文件
    file_path = attachment_to_delete.get("file_path")
    if file_path:
        delete_uploaded_file(file_path)
    
    # 从列表中移除
    attachments.remove(attachment_to_delete)
    
    # 更新数据库，手动json序列化
    from backend.app.models import Project as ProjectModel
    db.query(ProjectModel).filter(ProjectModel.id == project_id).update({
        "attachments": json.dumps(attachments, ensure_ascii=False) if attachments else None
    })
    db.commit()
    
    return {"message": "附件删除成功"}

